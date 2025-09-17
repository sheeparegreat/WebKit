# Copyright (C) 2025 Apple Inc. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1.  Redistributions of source code must retain the above copyright
#     notice, this list of conditions and the following disclaimer.
# 2.  Redistributions in binary form must reproduce the above copyright
#     notice, this list of conditions and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY APPLE INC. AND ITS CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL APPLE INC. OR ITS CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# If these type are in a 'opaque container' we are concerned
ODT_CONCERN = {
    "char", "signed char", "unsigned char", "int8_t", "uint8_t",
    "CFDataRef", "NSData", "WebKit::CoreIPCData",
    "CFDictionaryRef", "CFArrayRef", "NSDictionary",
    "MachSendRight", "MachSendRightAnnotated", "WTF::MachSendRightAnnotated",
    # NSArray to be added in a follow-up change
}

# These are by themselves opaque without a container
OPAQUE_TYPES = [
    "MachSendRight",
    "MachSendRightAnnotated",
    "WTF::MachSendRightAnnotated",
    "WTF::MachSendRightAnnotated",
    "CFDataRef", "NSData", "WebKit::CoreIPCData",
    "CFDictionaryRef", "CFArrayRef", "NSDictionary",
]

# Containers that represent actual opaque data transport when filled with ODT types
# These ARE opaque when they contain ODT concern types (uint8_t, char, CFDataRef, etc.)
OPAQUE_CONTAINERS = {
    "std::span": {"check_params": "first"},
    "std::array": {"check_params": "first", "special_parsing": "array_parsing"},
    "Vector": {"check_params": "first"},
    "FixedVector": {"check_params": "first"},
    "RetainPtr": {"check_params": "first"},
}

# Containers that should be decomposed to find opaque inner containers.
TRANSPARENT_CONTAINERS = {
    "Expected": {"check_params": "selective", "selective_indices": [0]},  # Only check T in Expected<T, E>
    "Variant": {"check_params": "all"},

    "std::pair": {"check_params": "all"},
    "std::tuple": {"check_params": "all"},
    "KeyValuePair": {"check_params": "all"},
    "OptionalTuple": {"check_params": "all"},
    "IPC::ArrayReferenceTuple": {"check_params": "all"},

    "std::optional": {"check_params": "first"},
    "std::unique_ptr": {"check_params": "first"},
    "UniqueRef": {"check_params": "first"},
    "Ref": {"check_params": "first"},
    "RefPtr": {"check_params": "first"},

    "HashMap": {"check_params": "first_two"},
    "MemoryCompactRobinHoodHashMap": {"check_params": "first_two"},
    "MemoryCompactLookupOnlyRobinHoodHashSet": {"check_params": "first"},
    "HashSet": {"check_params": "first"},
    "OptionSet": {"check_params": "first"},
    "Markable": {"check_params": "first"},
    "HashCountedSet": {"check_params": "first"},
}

ALL_CONTAINER_CONFIGS = {**OPAQUE_CONTAINERS, **TRANSPARENT_CONTAINERS}


def _remove_const_and_whitespace(type_str):
    if not type_str:
        return ""
    type_str = type_str.strip()
    if type_str.startswith("const "):
        type_str = type_str[6:].strip()
    return type_str


def _split_template_parameters(param_list):
    """Split template parameters handling nested brackets properly

    Example: "Vector<uint8_t>, String, int" -> ["Vector<uint8_t>", "String", "int"]
    """
    if not param_list:
        return []

    parameters = []
    current_param = ""
    bracket_depth = 0

    for char in param_list:
        if char == '<':
            bracket_depth += 1
            current_param += char
        elif char == '>':
            bracket_depth -= 1
            current_param += char
        elif char == ',' and bracket_depth == 0:
            # Found a top-level comma - end of current parameter
            param = _remove_const_and_whitespace(current_param)
            if param:
                parameters.append(param)
            current_param = ""
        else:
            current_param += char

    # Add the last parameter
    param = _remove_const_and_whitespace(current_param)
    if param:
        parameters.append(param)

    return parameters


def _array_special_parsing(param_list):
    """Special parsing for std::array<T, N> - only return T, ignore N"""
    params = _split_template_parameters(param_list)
    return params[:1] if params else []


def _get_container_info(type_str):
    """Get container name and parameters from a type string
    Returns: (container_name, parameters_list, is_opaque_container) or (None, None, False) if not a container
    """
    for container_name in ALL_CONTAINER_CONFIGS:
        prefix = container_name + "<"
        if type_str.startswith(prefix) and type_str.endswith(">"):
            param_list = type_str[len(prefix):-1]

            # Handle special parsing cases
            config = ALL_CONTAINER_CONFIGS[container_name]
            if config.get("special_parsing") == "array_parsing":
                parameters = _array_special_parsing(param_list)
            else:
                parameters = _split_template_parameters(param_list)

            is_opaque_container = container_name in OPAQUE_CONTAINERS
            return container_name, parameters, is_opaque_container

    return None, None, False


def _get_parameters_to_check(container_name, parameters):
    """Get the list of parameters to check based on container config"""
    if not parameters:
        return []

    config = ALL_CONTAINER_CONFIGS.get(container_name, {})
    check_params = config.get("check_params", "all")

    if check_params == "first":
        return parameters[:1]
    elif check_params == "first_two":
        return parameters[:2]
    elif check_params == "all":
        return parameters
    elif check_params == "selective":
        indices = config.get("selective_indices", [])
        return [parameters[i] for i in indices if i < len(parameters)]
    else:
        return []


def _contains_opaque_data(type_str, visited=None, from_opaque_container=False):
    """Check if a type contains opaque data and return the ODT concern type if found.

    Args:
        type_str: The type string to check
        visited: Set of already visited types to avoid infinite recursion
        from_opaque_container: True if we're checking from within an opaque container context
    """
    if visited is None:
        visited = set()

    # Avoid infinite recursion
    if type_str in visited:
        return None
    visited.add(type_str)

    clean_type = _remove_const_and_whitespace(type_str)

    if clean_type in OPAQUE_TYPES:
        return clean_type

    # Direct ODT concerns are only opaque when we're in an opaque container context
    if _is_odt_concern(clean_type) and from_opaque_container:
        return clean_type

    container_name, parameters, is_opaque_container = _get_container_info(clean_type)

    if not container_name or not parameters:
        return None

    params_to_check = _get_parameters_to_check(container_name, parameters)

    # For opaque containers, check parameters in opaque container context
    if is_opaque_container:
        for param in params_to_check:
            result = _contains_opaque_data(param, visited.copy(), from_opaque_container=True)
            if result is not None:
                return result

    # For transparent containers, handle different types differently
    else:
        # Simple wrapper containers (std::optional, RetainPtr) can contain direct ODT concerns
        simple_wrappers = ["std::optional", "RetainPtr"]
        is_simple_wrapper = container_name in simple_wrappers

        for param in params_to_check:
            clean_param = _remove_const_and_whitespace(param)

            # Special case: RetainPtr can contain direct opaque types
            if clean_param in OPAQUE_TYPES and container_name in ["RetainPtr"]:
                return clean_param

            # Simple wrappers can propagate ODT concerns when in opaque container context
            if is_simple_wrapper and _is_odt_concern(clean_param) and from_opaque_container:
                return clean_param

            # Simple wrappers preserve the opaque container context, structural containers reset it
            next_context = from_opaque_container if is_simple_wrapper else False
            result = _contains_opaque_data(param, visited.copy(), from_opaque_container=next_context)
            if result is not None:
                return result

    return None


def _is_odt_concern(type_str):
    return type_str.strip() in ODT_CONCERN


def is_opaque_type(type):
    """Check if a type represents opaque data transport

    Returns true if we have an opaque data type:
    1. Direct opaque types (MachSendRight, etc.) -> True
    2. Opaque containers with ODT concerns (Vector<uint8_t>, etc.) -> True
    3. Transparent containers containing opaque containers with ODT concerns (std::pair<Vector<uint8_t>, String>) -> True
    4. Transparent containers without opaque types (std::pair<uint8_t, String>) -> False
    5. Non-containers -> False
    """
    return _contains_opaque_data(type) is not None


if __name__ == '__main__':
    import unittest

    class TestOpaqueTypes(unittest.TestCase):

        def test_is_odt_concern_function(self):
            for odt_type in ODT_CONCERN:
                self.assertTrue(_is_odt_concern(odt_type), f"Expected {odt_type} to be ODT concern")

            non_odt_types = ['String', 'int', 'float', 'bool', 'WTF::UUID']
            for non_odt_type in non_odt_types:
                self.assertFalse(_is_odt_concern(non_odt_type), f"Expected {non_odt_type} to not be ODT concern")

        def test_contains_opaque_data_function(self):
            # Test opaque containers with ODT concerns
            self.assertEqual(_contains_opaque_data("std::span<uint8_t>"), "uint8_t")
            self.assertEqual(_contains_opaque_data("std::span<const uint8_t>"), "uint8_t")
            self.assertEqual(_contains_opaque_data("Vector<char>"), "char")
            self.assertEqual(_contains_opaque_data("Vector<const char>"), "char")
            self.assertEqual(_contains_opaque_data("std::array<uint8_t, 24>"), "uint8_t")
            self.assertEqual(_contains_opaque_data("std::array<const uint8_t, 16>"), "uint8_t")
            self.assertEqual(_contains_opaque_data("RetainPtr<CFDataRef>"), "CFDataRef")
            self.assertEqual(_contains_opaque_data("Vector<MachSendRight>"), "MachSendRight")

            # Test nested containers
            self.assertEqual(_contains_opaque_data("std::optional<Vector<uint8_t>>"), "uint8_t")
            self.assertEqual(_contains_opaque_data("Vector<std::optional<uint8_t>>"), "uint8_t")
            self.assertEqual(_contains_opaque_data("Vector<std::pair<Vector<uint8_t>, std::optional<WTF::UUID>>>"), "uint8_t")
            self.assertEqual(_contains_opaque_data("Variant<Vector<uint8_t>, String>"), "uint8_t")

            # Test transparent containers without opaque content
            self.assertIsNone(_contains_opaque_data("Expected<uint8_t, String>"))
            self.assertIsNone(_contains_opaque_data("Variant<uint8_t, String>"))
            self.assertIsNone(_contains_opaque_data("std::pair<uint8_t, String>"))
            self.assertIsNone(_contains_opaque_data("std::optional<uint8_t>"))
            self.assertIsNone(_contains_opaque_data("uint8_t"))
            self.assertIsNone(_contains_opaque_data("String"))

        def test_direct_opaque_types(self):
            self.assertTrue(is_opaque_type("MachSendRight"))
            self.assertTrue(is_opaque_type("MachSendRightAnnotated"))
            self.assertFalse(is_opaque_type("String"))
            self.assertFalse(is_opaque_type("int"))

        def test_container_types_with_odt_concerns(self):
            self.assertTrue(is_opaque_type("std::optional<Vector<uint8_t>>"))
            self.assertTrue(is_opaque_type("Vector<std::optional<uint8_t>>"))
            self.assertTrue(is_opaque_type("std::span<uint8_t>"))
            self.assertTrue(is_opaque_type("std::span<const uint8_t>"))
            self.assertTrue(is_opaque_type("std::span<char>"))
            self.assertTrue(is_opaque_type("std::span<const char>"))
            self.assertTrue(is_opaque_type("std::array<uint8_t, 24>"))
            self.assertTrue(is_opaque_type("std::array<const uint8_t, 16>"))
            self.assertTrue(is_opaque_type("Vector<uint8_t>"))
            self.assertTrue(is_opaque_type("Vector<const uint8_t>"))
            self.assertTrue(is_opaque_type("Vector<char>"))
            self.assertTrue(is_opaque_type("RetainPtr<CFDataRef>"))
            self.assertTrue(is_opaque_type("RetainPtr<NSData>"))
            self.assertTrue(is_opaque_type("std::optional<Vector<uint8_t>>"))
            self.assertTrue(is_opaque_type("Expected<Vector<uint8_t>, String>"))
            self.assertTrue(is_opaque_type("Variant<Vector<uint8_t>, String>"))
            self.assertTrue(is_opaque_type("std::pair<Vector<uint8_t>, String>"))
            self.assertTrue(is_opaque_type("std::pair<String, Vector<uint8_t>>"))
            self.assertTrue(is_opaque_type("Vector<std::pair<Vector<uint8_t>, std::optional<WTF::UUID>>>"))
            self.assertTrue(is_opaque_type("std::optional<Vector<std::pair<Vector<uint8_t>, String>>>"))
            self.assertTrue(is_opaque_type("HashMap<String, FixedVector<uint8_t>>"))
            self.assertTrue(is_opaque_type("HashSet<Vector<uint8_t>>"))
            self.assertTrue(is_opaque_type("std::unique_ptr<Vector<uint8_t>>"))
            self.assertTrue(is_opaque_type("KeyValuePair<Vector<uint8_t>, String>"))
            self.assertTrue(is_opaque_type("Vector<HashMap<String, std::pair<Vector<uint8_t>, int>>>"))
            self.assertTrue(is_opaque_type("Variant<Vector<uint8_t>, WebKit::HTTPBody::Element::FileData, String>"))
            self.assertTrue(is_opaque_type("Expected<std::pair<Vector<uint8_t>, String>, String>"))
            self.assertTrue(is_opaque_type("Vector<std::pair<Vector<uint8_t>, std::optional<WTF::UUID>>>"))
            self.assertTrue(is_opaque_type("std::optional<Vector<std::pair<Vector<uint8_t>, String>>>"))
            self.assertTrue(is_opaque_type("Variant<Vector<uint8_t>, WebKit::HTTPBody::Element::FileData, String>"))
            self.assertTrue(is_opaque_type("Variant<Vector<uint8_t>, Ref<WebCore::SharedBuffer>, URL>"))

        def test_container_types_without_odt_concerns(self):
            self.assertFalse(is_opaque_type("std::span<String>"))
            self.assertFalse(is_opaque_type("std::array<int, 5>"))
            self.assertFalse(is_opaque_type("Vector<String>"))
            self.assertFalse(is_opaque_type("std::optional<String>"))
            self.assertFalse(is_opaque_type("std::optional<uint8_t>"))
            self.assertFalse(is_opaque_type("Expected<uint8_t, String>"))
            self.assertFalse(is_opaque_type("Expected<String, uint8_t>"))
            self.assertFalse(is_opaque_type("Expected<String, int>"))
            self.assertFalse(is_opaque_type("Variant<uint8_t, int>"))
            self.assertFalse(is_opaque_type("Variant<String, int>"))
            self.assertFalse(is_opaque_type("std::pair<uint8_t, String>"))
            self.assertFalse(is_opaque_type("std::optional<std::pair<uint8_t, String>>"))
            self.assertFalse(is_opaque_type("Vector<std::pair<uint8_t, String>>"))

        def test_infinite_recursion_protection(self):
            """Test that the algorithm handles circular type references without infinite recursion"""
            # Create a visited set that simulates a circular reference
            visited = {"TestType"}

            # This should return None due to the visited check, not cause infinite recursion
            result = _contains_opaque_data("TestType", visited=visited)
            self.assertIsNone(result)

            # Test with a type that would normally be opaque but is already visited
            visited_opaque = {"Vector<uint8_t>"}
            result = _contains_opaque_data("Vector<uint8_t>", visited=visited_opaque)
            self.assertIsNone(result)

            # Verify normal operation still works when not visited
            result = _contains_opaque_data("Vector<uint8_t>")
            self.assertEqual(result, "uint8_t")

        def test_bad_formatting(self):
            """Test edge cases and malformed input"""
            self.assertFalse(is_opaque_type(""))
            self.assertFalse(is_opaque_type("Vector<>"))
            self.assertFalse(is_opaque_type("std::optional<>"))
            self.assertFalse(is_opaque_type("Vector"))
            self.assertFalse(is_opaque_type("std::optional"))
            self.assertFalse(is_opaque_type("<uint8_t>"))

    unittest.main()
