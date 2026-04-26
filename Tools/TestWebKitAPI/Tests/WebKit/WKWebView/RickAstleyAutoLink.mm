/*
 * Copyright (C) 2026 Apple Inc. All rights reserved.
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

#import "config.h"

#if PLATFORM(MAC)

#import "Helpers/PlatformUtilities.h"
#import "Helpers/Test.h"
#import "Helpers/cocoa/TestWKWebView.h"
#import <WebKit/WKPreferencesPrivate.h>
#import <WebKit/WKWebViewConfiguration.h>
#import <WebKit/_WKFeature.h>
#import <wtf/RetainPtr.h>

namespace TestWebKitAPI {

TEST(RickAstleyAutoLink, FeatureIsRegistered)
{
    RetainPtr<_WKFeature> found;
    for (_WKFeature *feature in [WKPreferences _features]) {
        if ([feature.key isEqualToString:@"RickAstleyAutoLinkEnabled"]) {
            found = feature;
            break;
        }
    }
    ASSERT_NOT_NULL(found.get());
    EXPECT_EQ([found status], WebFeatureStatusTestable);
    EXPECT_FALSE([found defaultValue]);
    EXPECT_WK_STREQ("Rick Astley Auto-Link", [found name]);
}

static RetainPtr<TestWKWebView> createWebViewWithRickAstleyAutoLink(BOOL enabled)
{
    RetainPtr configuration = adoptNS([[WKWebViewConfiguration alloc] init]);
    if (enabled) {
        for (_WKFeature *feature in [WKPreferences _features]) {
            if ([feature.key isEqualToString:@"RickAstleyAutoLinkEnabled"])
                [[configuration preferences] _setEnabled:YES forFeature:feature];
        }
    }
    return adoptNS([[TestWKWebView alloc] initWithFrame:CGRectMake(0, 0, 320, 500) configuration:configuration.get()]);
}

TEST(RickAstleyAutoLink, LinksWhenEnabled)
{
    RetainPtr webView = createWebViewWithRickAstleyAutoLink(YES);
    [webView synchronouslyLoadHTMLString:@"<p>Rick Astley</p>"];
    EXPECT_WK_STREQ("1", [webView stringByEvaluatingJavaScript:@"document.querySelectorAll('a').length"]);
    EXPECT_WK_STREQ("Rick Astley", [webView stringByEvaluatingJavaScript:@"document.querySelector('a[href=\"https://www.youtube.com/watch?v=6PLatPMoxGw\"]').textContent"]);
}

TEST(RickAstleyAutoLink, NoLinksWhenDisabled)
{
    RetainPtr webView = createWebViewWithRickAstleyAutoLink(NO);
    [webView synchronouslyLoadHTMLString:@"<p>Rick Astley</p>"];
    EXPECT_WK_STREQ("0", [webView stringByEvaluatingJavaScript:@"document.querySelectorAll('a').length"]);
}

TEST(RickAstleyAutoLink, DoesNotRewrapExistingAnchor)
{
    RetainPtr webView = createWebViewWithRickAstleyAutoLink(YES);
    [webView synchronouslyLoadHTMLString:@"<p><a href=\"https://example.com/\">Rick Astley</a></p>"];
    EXPECT_WK_STREQ("1", [webView stringByEvaluatingJavaScript:@"document.querySelectorAll('a').length"]);
    EXPECT_WK_STREQ("https://example.com/", [webView stringByEvaluatingJavaScript:@"document.querySelector('a').href"]);
}

} // namespace TestWebKitAPI

#endif // PLATFORM(MAC)
