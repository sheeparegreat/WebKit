/*
 * Copyright (C) 2021-2023 Apple Inc. All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1.  Redistributions of source code must retain the above copyright
 *     notice, this list of conditions and the following disclaimer.
 * 2.  Redistributions in binary form must reproduce the above copyright
 *     notice, this list of conditions and the following disclaimer in the
 *     documentation and/or other materials provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY APPLE INC. AND ITS CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL APPLE INC. OR ITS CONTRIBUTORS BE LIABLE FOR
 * ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

#pragma once

#include "ArgumentCoders.h"
#include "Connection.h"
#include "MessageNames.h"
#include <wtf/Forward.h>
#include <wtf/RuntimeApplicationChecks.h>
#include <wtf/ThreadSafeRefCounted.h>


namespace Messages {
namespace TestWithOpaqueTransports {

static inline IPC::ReceiverName messageReceiverName()
{
#if ASSERT_ENABLED
    static std::once_flag onceFlag;
    std::call_once(
        onceFlag,
        [&] {
            ASSERT(!isInAuxiliaryProcess());
        }
    );
#endif
    return IPC::ReceiverName::TestWithOpaqueTransports;
}

class HandlePort {
public:
    using Arguments = std::tuple<TestGenerationMachPort>;

    static IPC::MessageName name() { return IPC::MessageName::TestWithOpaqueTransports_HandlePort; }
    static constexpr bool isSync = false;
    static constexpr bool canDispatchOutOfOrder = false;
    static constexpr bool replyCanDispatchOutOfOrder = false;
    static constexpr bool deferSendingIfSuspended = false;

    explicit HandlePort(const TestGenerationMachPort& port)
        : m_port(port)
    {
        ASSERT(isInNetworkProcess());
    }

    template<typename Encoder>
    void encode(Encoder& encoder)
    {
        SUPPRESS_FORWARD_DECL_ARG encoder << m_port;
    }

private:
    SUPPRESS_FORWARD_DECL_MEMBER const TestGenerationMachPort& m_port;
};

class HandleSpan {
public:
    using Arguments = std::tuple<ResumeDownloadOpaqueData>;

    static IPC::MessageName name() { return IPC::MessageName::TestWithOpaqueTransports_HandleSpan; }
    static constexpr bool isSync = false;
    static constexpr bool canDispatchOutOfOrder = false;
    static constexpr bool replyCanDispatchOutOfOrder = false;
    static constexpr bool deferSendingIfSuspended = false;

    explicit HandleSpan(const ResumeDownloadOpaqueData& data)
        : m_data(data)
    {
        ASSERT(isInNetworkProcess());
    }

    template<typename Encoder>
    void encode(Encoder& encoder)
    {
        RELEASE_ASSERT_WITH_SECURITY_IMPLICATION(!isInWebProcess());
        SUPPRESS_FORWARD_DECL_ARG encoder << m_data;
    }

private:
    SUPPRESS_FORWARD_DECL_MEMBER const ResumeDownloadOpaqueData& m_data;
};

class ThrowThisOverTheWall {
public:
    using Arguments = std::tuple<SomethingElseParsesThisOpaqueData>;

    static IPC::MessageName name() { return IPC::MessageName::TestWithOpaqueTransports_ThrowThisOverTheWall; }
    static constexpr bool isSync = false;
    static constexpr bool canDispatchOutOfOrder = false;
    static constexpr bool replyCanDispatchOutOfOrder = false;
    static constexpr bool deferSendingIfSuspended = false;

    explicit ThrowThisOverTheWall(const SomethingElseParsesThisOpaqueData& probablyBad)
        : m_probablyBad(probablyBad)
    {
        ASSERT(isInNetworkProcess());
    }

    template<typename Encoder>
    void encode(Encoder& encoder)
    {
        SUPPRESS_FORWARD_DECL_ARG encoder << m_probablyBad;
    }

private:
    SUPPRESS_FORWARD_DECL_MEMBER const SomethingElseParsesThisOpaqueData& m_probablyBad;
};

class RenderBitmap {
public:
    using Arguments = std::tuple<PixelOpaqueData>;

    static IPC::MessageName name() { return IPC::MessageName::TestWithOpaqueTransports_RenderBitmap; }
    static constexpr bool isSync = false;
    static constexpr bool canDispatchOutOfOrder = false;
    static constexpr bool replyCanDispatchOutOfOrder = false;
    static constexpr bool deferSendingIfSuspended = false;

    explicit RenderBitmap(const PixelOpaqueData& pixels)
        : m_pixels(pixels)
    {
        ASSERT(isInNetworkProcess());
    }

    template<typename Encoder>
    void encode(Encoder& encoder)
    {
        SUPPRESS_FORWARD_DECL_ARG encoder << m_pixels;
    }

private:
    SUPPRESS_FORWARD_DECL_MEMBER const PixelOpaqueData& m_pixels;
};

} // namespace TestWithOpaqueTransports
} // namespace Messages
