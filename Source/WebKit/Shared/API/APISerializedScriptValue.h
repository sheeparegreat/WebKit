/*
 * Copyright (C) 2010 Apple Inc. All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY APPLE INC. AND ITS CONTRIBUTORS ``AS IS''
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
 * THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 * PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL APPLE INC. OR ITS CONTRIBUTORS
 * BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
 * SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
 * CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
 * THE POSSIBILITY OF SUCH DAMAGE.
 */

#pragma once

#include "APIObject.h"
#include "WKRetainPtr.h"
#include <JavaScriptCore/JSRetainPtr.h>
#include <WebCore/CryptoKey.h>
#include <WebCore/SerializedScriptValue.h>
#include <wtf/RefPtr.h>
#include <wtf/RuntimeApplicationChecks.h>

#if USE(GLIB)
#include <wtf/glib/GRefPtr.h>

typedef struct _GVariant GVariant;
typedef struct _JSCContext JSCContext;
typedef struct _JSCValue JSCValue;
#endif

typedef const void* WKTypeRef;

namespace API {

class SerializedScriptValue : public API::ObjectImpl<API::Object::Type::SerializedScriptValue> {
public:
    static Ref<SerializedScriptValue> create(Ref<WebCore::SerializedScriptValue>&& serializedValue)
    {
        return adoptRef(*new SerializedScriptValue(WTFMove(serializedValue)));
    }
    
    static RefPtr<SerializedScriptValue> create(JSContextRef context, JSValueRef value, JSValueRef* exception)
    {
        RefPtr<WebCore::SerializedScriptValue> serializedValue = WebCore::SerializedScriptValue::create(context, value, exception);
        if (!serializedValue)
            return nullptr;
        return adoptRef(*new SerializedScriptValue(serializedValue.releaseNonNull()));
    }
    
    static Ref<SerializedScriptValue> createFromWireBytes(std::span<const uint8_t> buffer)
    {
        return adoptRef(*new SerializedScriptValue(WebCore::SerializedScriptValue::createFromWireBytes(Vector<uint8_t>(buffer))));
    }
    
    static Ref<SerializedScriptValue> createFromWireBytes(std::span<const uint8_t> buffer, WebCore::SerializationTypeFilter filter)
    {
        bool typesAreLimited = filter != WebCore::SerializationTypeFilter::None;
        bool typesAppropriatelyRestricted = !isInAuxiliaryProcess() ? typesAreLimited : true;
        RELEASE_ASSERT_WITH_SECURITY_IMPLICATION(typesAppropriatelyRestricted);

        return adoptRef(*new SerializedScriptValue(WebCore::SerializedScriptValue::createFromWireBytes(Vector<uint8_t>(buffer), filter)));
    }

    JSValueRef deserialize(JSContextRef context, JSValueRef* exception)
    {
        return m_serializedScriptValue->deserialize(context, exception);
    }

    static WKRetainPtr<WKTypeRef> deserializeWK(WebCore::SerializedScriptValue&);
    static Vector<uint8_t> serializeCryptoKey(const WebCore::CryptoKey&);

#if PLATFORM(COCOA) && defined(__OBJC__)
    static id deserialize(WebCore::SerializedScriptValue&);
    static RefPtr<SerializedScriptValue> createFromNSObject(id);
    static JSRetainPtr<JSGlobalContextRef> deserializationContext();
#endif

#if USE(GLIB)
    static JSCContext* sharedJSCContext();
    static GRefPtr<JSCValue> deserialize(WebCore::SerializedScriptValue&);
    static RefPtr<SerializedScriptValue> createFromGVariant(GVariant*);
    static RefPtr<SerializedScriptValue> createFromJSCValue(JSCValue*);
#endif

    std::span<const uint8_t> dataReference() const { return m_serializedScriptValue->wireBytes(); }

    WebCore::SerializedScriptValue& internalRepresentation() { return m_serializedScriptValue.get(); }

private:
    explicit SerializedScriptValue(Ref<WebCore::SerializedScriptValue>&& serializedScriptValue)
        : m_serializedScriptValue(WTFMove(serializedScriptValue))
    {
    }

    const Ref<WebCore::SerializedScriptValue> m_serializedScriptValue;
};
    
}

SPECIALIZE_TYPE_TRAITS_API_OBJECT(SerializedScriptValue);
