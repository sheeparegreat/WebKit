/*
 * Copyright (C) 2017 Apple Inc. All rights reserved.
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
 * THIS SOFTWARE IS PROVIDED BY APPLE INC. ``AS IS'' AND ANY
 * EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 * PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL APPLE INC. OR
 * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
 * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
 * PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
 * OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 * (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. 
 */

#pragma once

#if !BUSE(TZONE)

#include "FixedVector.h"
#include "IsoPage.h"
#include "Mutex.h"

#if !BUSE(LIBPAS)

namespace bmalloc {

template<typename Config>
class IsoDeallocator {
public:
    static constexpr unsigned logsPerPage = 2;
    static constexpr unsigned logCapacity =
        (IsoPageBase::pageSize / Config::objectSize + logsPerPage - 1) / logsPerPage;
    
    IsoDeallocator(Mutex& lock);
    ~IsoDeallocator();
    
    template<typename Type>
    void deallocate(api::IsoHeapBase<Type>&, void* p);
    void scavenge();
    
private:
    Mutex* m_lock;
    FixedVector<void*, logCapacity> m_objectLog;
};

} // namespace bmalloc

#endif
#endif // !BUSE(TZONE)
