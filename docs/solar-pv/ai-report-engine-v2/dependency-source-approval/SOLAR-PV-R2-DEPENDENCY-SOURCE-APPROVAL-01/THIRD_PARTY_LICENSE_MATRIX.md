# 第三方许可证初审与逐项义务

审阅范围 42 名称/43精确版本；官方 tag 文本覆盖 39名称/40版本，所有再分发 BLOCKED，绝非法律 PASS。
以下引用分析员逐项义务原文，保留其 exact scope、HTTP/SHA 和差异，不用 MIT/BSD 标签替代实际许可证/NOTICE。

- beautifulsoup4：文档 title=4.14.3、body=4.15.0，不能 pin 为精确许可证据。
- cobble：0.1.4/v0.1.4 的 LICENSE/LICENSE.txt 均 404，不能据 installed 字段放行。
- protobuf：有 v36.2 LICENSE，但 7.36.2→tag/官方关联未证。
- lxml：BSD root 不覆盖 binary iconv LGPL-2.1、ElementTree/PSF、schema/XSL 等例外；实际 linking/source/relink 路径待构件与法律核查。
- Pillow 为 MIT-CMU，不是普通 MIT；certifi 的 MPL-2.0 covered-source 提供途径待核。
- cffi MIT-0、PSF 包的变更摘要、packaging/cryptography/dateutil 双许可选择需分别记录。
- numpy/onnxruntime/cryptography/pypdfium2 的 bundled/native NOTICE 需按实际平台 wheel 裁定；仓库聚合文本或 404 不证明 wheel 无 NOTICE。

这是工程尽调，商业再分发仍需权利人/法律审核。脱敏分享文本不是可直接随二进制再分发的完整 legal notice。

---

# 42 依赖许可证工程初审（不是法律批准）

所有 LICENSE_REVIEW / REDISTRIBUTION_GATE 均为 **BLOCKED**；wheel 内 LICENSE/NOTICE 字节对照恒为 **ARTIFACT_NOT_ACQUIRED**。

|依赖|观察版本|官方文本 scope|初步许可证解释|阻塞|
|---|---|---|---|---|
|attrs|26.1.0|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|MIT|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|beautifulsoup4|4.15.0|UNKNOWN_OR_DIFFERENT_SCOPE|UNKNOWN|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|certifi|2026.10.23|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|MPL-2.0|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|cffi|2.1.1|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|MIT-0|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|charset-normalizer|3.5.2|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|MIT|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|click|8.5.1|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|BSD-3-Clause|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|cobble|0.1.4|UNKNOWN_OR_DIFFERENT_SCOPE|UNKNOWN|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|cryptography|50.0.2|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|Apache-2.0 OR BSD-3-Clause|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|defusedxml|0.7.1|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|PSF-2.0|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|et-xmlfile|2.0.0|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|UNKNOWN|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|flatbuffers|25.12.19|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|Apache-2.0|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|idna|3.20|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|BSD-3-Clause|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|jsonschema|4.26.0|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|MIT|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|jsonschema-specifications|2025.9.1|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|MIT|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|lxml|6.1.3|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|BSD-3-Clause|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|magika|1.0.3|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|Apache-2.0|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|mammoth|1.13.0|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|BSD-2-Clause|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|markdownify|1.2.3|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|MIT|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|markitdown|0.1.9|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|MIT|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|numpy|2.5.4|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|BSD-3-Clause|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|onnxruntime|1.31.1|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|MIT|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|openpyxl|3.1.5|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|UNKNOWN|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|packaging|26.3|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|Apache-2.0 OR BSD-3-Clause|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|pandas|3.1.1|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|BSD-3-Clause|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|pdfminer-six|20260107|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|MIT|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|pdfplumber|0.11.10|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|MIT|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|pillow|12.3.0|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|MIT-CMU|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|protobuf|7.36.2|UNKNOWN_OR_DIFFERENT_SCOPE|BSD-3-Clause|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|pycparser|3.12|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|BSD-3-Clause|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|pypdfium2|5.15.1|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|Apache-2.0 OR BSD-3-Clause|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|python-dateutil|4.0.0|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|Apache-2.0 OR BSD-3-Clause|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|python-docx|1.2.0|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|MIT|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|python-pptx|1.0.2|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|MIT|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|referencing|0.37.0|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|MIT|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|requests|2.34.2|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|Apache-2.0|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|rpds-py|2026.9.1|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|MIT|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|six|1.17.0|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|MIT|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|soupsieve|4.0.1|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|MIT|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|typing-extensions|4.16.0|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|PSF-2.0|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|tzdata|2026.5, 2026.6|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND<br>EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|Apache-2.0<br>Apache-2.0|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|urllib3|2.8.0|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|MIT|BLOCKED; ARTIFACT_NOT_ACQUIRED|
|xlsxwriter|3.3.1|EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND|BSD-2-Clause|BLOCKED; ARTIFACT_NOT_ACQUIRED|

## attrs

### 26.1.0 — BLOCKED
- 官方 SPDX: `MIT`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Retain actual copyright and permission text with substantial copies, including redistribution notices. No implied warranty or trademark endorsement.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/python-attrs/attrs/26.1.0/LICENSE; HTTP 200; SHA 882115c95dfc2af1eeb6714f8ec6d5cbcabf667caff8729f42420da63f714e9f

## beautifulsoup4

### 4.15.0 — BLOCKED
- 官方 SPDX: `None`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: UNKNOWN_OR_DIFFERENT_SCOPE
- Official project docs fetched but not pinned 4.15.0 license text. HTML title says 4.14.3 while body says 4.15.0; no silent relabeling of latest/project documentation as an exact artifact license.
- Do not redistribute until precise version license, copyright chain and artifact-native notices are established.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- EXACT_VERSION_OFFICIAL_LICENSE_TEXT_OR_LINK_NOT_ESTABLISHED
- VERSION_LICENSE_REVIEW_UNRESOLVED
- 来源: https://www.crummy.com/software/BeautifulSoup/bs4/doc/; HTTP 200; SHA 3bf48f50f08a262974d276deec854e7ec90c73788e85f779fa0120380dbda790

## certifi

### 2026.10.23 — BLOCKED
- 官方 SPDX: `None`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Exact-tag LICENSE says Mozilla-derived root certificate bundle subject to MPL-2.0; canonical MPL full text saved. Certificate-source/update chain and covered files must be checked in actual wheel.
- File-level copyleft: make covered source including modifications available by a reasonable means and notify recipients how to obtain it; retain license/substance of notices and furnish license. Larger-work proprietary files are not automatically MPL. Confirm actual covered files and executable/source distribution route with legal review.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/certifi/python-certifi/2026.10.23/LICENSE; HTTP 200; SHA e93716da6b9c0d5a4a1df60fe695b370f0695603d21f6f83f053e42cfc10caf7
- 来源: https://www.mozilla.org/media/MPL/2.0/index.txt; HTTP 200; SHA 3f3d9e0024b1921b067d6f7f88deb4a60cbe7a78e76c64e3f1d7fc3b779b9d04

## cffi

### 2.1.1 — BLOCKED
- 官方 SPDX: `MIT-0`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Exact-tag LICENSE says MIT No Attribution, with explicit exceptions; libffi in native builds must be checked separately, not reclassified MIT-0 by inheritance.
- Primary MIT No Attribution does not require attribution; do not omit licenses or notices of excepted third-party components.
- libffi and platform-native bindings; actual bundled component versions and licenses required.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- BUNDLED_NATIVE_OR_ASSET_LICENSE_CLOSURE_UNRESOLVED
- 来源: https://raw.githubusercontent.com/python-cffi/cffi/v2.1.1/LICENSE; HTTP 200; SHA 5ba24ddc57067f9249add644c3afc41a5d6dc37e23433ef759d95df370b0af63

## charset-normalizer

### 3.5.2 — BLOCKED
- 官方 SPDX: `None`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Retain actual copyright and permission text with substantial copies, including redistribution notices. No implied warranty or trademark endorsement.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/jawah/charset_normalizer/3.5.2/LICENSE; HTTP 200; SHA 6d0d41bfe170ac6c7dc248c9a63e254d0fb45a60d50a8257d0af92c6e249b887

## click

### 8.5.1 — BLOCKED
- 官方 SPDX: `BSD-3-Clause`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Retain copyright, conditions and disclaimer in source and binary distribution materials; no author/contributor endorsement without permission.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/pallets/click/8.5.1/LICENSE.txt; HTTP 200; SHA 9a8ad106a394e853bfe21f42f4e72d592819a22805d991b5f3275029292b658d

## cobble

### 0.1.4 — BLOCKED
- 官方 SPDX: `None`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: UNKNOWN_OR_DIFFERENT_SCOPE
- Official exact metadata declaration available but both 0.1.4/v0.1.4 LICENSE and LICENSE.txt text attempts returned 404. Do not infer artifact permission from installed metadata or latest tag.
- Do not redistribute until precise version license, copyright chain and artifact-native notices are established.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- EXACT_VERSION_OFFICIAL_LICENSE_TEXT_OR_LINK_NOT_ESTABLISHED
- VERSION_LICENSE_REVIEW_UNRESOLVED

## cryptography

### 50.0.2 — BLOCKED
- 官方 SPDX: `Apache-2.0 OR BSD-3-Clause`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Exact-tag LICENSE selects Apache-2.0 or BSD; both complete texts saved. Install documentation confirms Windows statically linked wheel. OpenSSL/Rust/vendor closure requires exact binary versions and license notices; NOTICE 404 does not prove absence in wheel.
- Choose and document a permitted license route for the relevant project code; do not erase differently licensed historical/vendored component notices. Apply corresponding Apache or BSD obligations.
- OpenSSL and Rust/native dependency versions, build flags, embedded notices and source/provenance chain required.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- BUNDLED_NATIVE_OR_ASSET_LICENSE_CLOSURE_UNRESOLVED
- 来源: https://raw.githubusercontent.com/pyca/cryptography/50.0.2/LICENSE; HTTP 200; SHA 3e0c7c091a948b82533ba98fd7cbb40432d6f1a9acbf85f5922d2f99a93ae6bb
- 来源: https://raw.githubusercontent.com/pyca/cryptography/50.0.2/LICENSE.APACHE; HTTP 200; SHA aac73b3148f6d1d7111dbca32099f68d26c644c6813ae1e4f05f6579aa2663fe
- 来源: https://raw.githubusercontent.com/pyca/cryptography/50.0.2/LICENSE.BSD; HTTP 200; SHA 602c4c7482de6479dd2e9793cda275e5e63d773dacd1eca689232ab7008fb4fb

## defusedxml

### 0.7.1 — BLOCKED
- 官方 SPDX: `None`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Exact-tag PSF-2.0 full text captured; retain notices/change-summary requirements.
- Retain PSF license and copyright; when distributing derivative versions include a brief summary of changes; no implied PSF endorsement. Preserve any additional historical or embedded code licenses.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/tiran/defusedxml/v0.7.1/LICENSE; HTTP 200; SHA b80ce9da8c42a1f91079627fbbe2bf27210ae108a0ffe5f077d5b08e076c24c8

## et-xmlfile

### 2.0.0 — BLOCKED
- 官方 SPDX: `None`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Do not redistribute until precise version license, copyright chain and artifact-native notices are established.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://foss.heptapod.net/openpyxl/et_xmlfile/-/raw/2.0.0/LICENCE.rst; HTTP 200; SHA 0c84bb42f5d367e5ebf9fc2dde35b16141df5ee0fdc189250858bc6c5560f69e

## flatbuffers

### 25.12.19 — BLOCKED
- 官方 SPDX: `None`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Provide Apache-2.0 text; preserve pertinent copyright/patent/trademark/attribution notices; mark modified files; if supplied, reproduce NOTICE attribution in a readable compliant place. Patent grant/termination applies; no trademark grant.
- Capture native or generated runtime scope if included; Python project license does not automatically cover external consumers.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- BUNDLED_NATIVE_OR_ASSET_LICENSE_CLOSURE_UNRESOLVED
- 来源: https://raw.githubusercontent.com/google/flatbuffers/v25.12.19/LICENSE; HTTP 200; SHA cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30

## idna

### 3.20 — BLOCKED
- 官方 SPDX: `BSD-3-Clause`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Retain copyright, conditions and disclaimer in source and binary distribution materials; no author/contributor endorsement without permission.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/kjd/idna/v3.20/LICENSE.md; HTTP 200; SHA 1a9a4f0e3d479a27240ddd59a9137a66ab4a0f9dfdc8ca6188cc0bfd85187f04

## jsonschema

### 4.26.0 — BLOCKED
- 官方 SPDX: `MIT`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Retain actual copyright and permission text with substantial copies, including redistribution notices. No implied warranty or trademark endorsement.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/python-jsonschema/jsonschema/v4.26.0/COPYING; HTTP 200; SHA 4f92a015a13c4d1a040bef018aa13430b4f1bc73b41b16bb846c346766de7439

## jsonschema-specifications

### 2025.9.1 — BLOCKED
- 官方 SPDX: `MIT`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Retain actual copyright and permission text with substantial copies, including redistribution notices. No implied warranty or trademark endorsement.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/python-jsonschema/jsonschema-specifications/v2025.9.1/COPYING; HTTP 200; SHA 42dcd63495f87b4eb7c7757afa379bb55a53f94afd7a5f657d9adf57236e515c

## lxml

### 6.1.3 — BLOCKED
- 官方 SPDX: `None`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- LICENSES.txt explicitly lists BSD, ElementTree/PSF code, schemas/XSL exceptions and bundled zlib/iconv/libxml2/libxslt/libexslt. iconv is LGPL-2.1; project BSD cannot clear whole native wheel. GPL test.py is a source test-runner exception, NOT proof production wheel is GPL. Some XSL are described as unlicensed, requiring actual wheel membership/copyright review.
- Retain copyright, conditions and disclaimer in source and binary distribution materials; no author/contributor endorsement without permission.
- Confirmed source notice lists iconv LGPL-2.1 plus zlib/libxml2/libxslt/libexslt; recover exact versions and linkage/object/relinkability information, corresponding source route, LGPL text and modification notices. Legal owner must decide permitted redistribution route; not all platforms assumed identical.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- BUNDLED_NATIVE_OR_ASSET_LICENSE_CLOSURE_UNRESOLVED
- LGPL_2_1_ICONV_AND_XSL_COPYRIGHT_REVIEW_REQUIRED
- 来源: https://raw.githubusercontent.com/lxml/lxml/lxml-6.1.3/LICENSES.txt; HTTP 200; SHA 388fa99f3bde4447cd5a4cbb114037be026854db6cfe89e112691c1d8abdcf3c
- 来源: https://raw.githubusercontent.com/lxml/lxml/lxml-6.1.3/LICENSE.txt; HTTP 200; SHA 8fc2b568133516e46845d2147917adeee1648e70ae9ab5ed6c5417afef4ce855
- 来源: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.txt; HTTP 200; SHA 20e50fe7aae3e56378ebf0417d9de904f55a0e61e4df315333e632a4d3555d95
- 来源: https://raw.githubusercontent.com/lxml/lxml/lxml-6.1.3/doc/licenses/GPL.txt; HTTP 200; SHA 32b1062f7da84967e7019d01ab805935caa7ab7321a7ced0e30ebe75e5df1670
- 来源: https://raw.githubusercontent.com/lxml/lxml/lxml-6.1.3/doc/licenses/elementtree.txt; HTTP 200; SHA 0497ae8138811ef4466ede653bab7a59feb3d3c14f9ed50fc33a00aeb5bec32e
- 来源: https://raw.githubusercontent.com/lxml/lxml/lxml-6.1.3/doc/licenses/BSD.txt; HTTP 200; SHA 69edb445c1335a8312d4c09271847e9956d84f0d9f724d125340cc3fad767b2a

## magika

### 1.0.3 — BLOCKED
- 官方 SPDX: `None`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Provide Apache-2.0 text; preserve pertinent copyright/patent/trademark/attribution notices; mark modified files; if supplied, reproduce NOTICE attribution in a readable compliant place. Patent grant/termination applies; no trademark grant.
- Repository metadata may cover wrapper, not sufficient model/data/native runtime assets. Do not download or run model. Future model-license/artifact/provenance approval is separate.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- BUNDLED_NATIVE_OR_ASSET_LICENSE_CLOSURE_UNRESOLVED
- 来源: https://raw.githubusercontent.com/google/magika/python-v1.0.3/LICENSE; HTTP 200; SHA 58d1e17ffe5109a7ae296caafcadfdbe6a7d176f0bc4ab01e12a689b0499d8bd

## mammoth

### 1.13.0 — BLOCKED
- 官方 SPDX: `None`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Retain copyright, conditions and disclaimer in source; reproduce them in documentation/materials accompanying binaries.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/mwilliamson/python-mammoth/1.13.0/LICENSE; HTTP 200; SHA 6663bbd049205d38a496ccacb412a151980b444627d38de218b3b809aef330f1

## markdownify

### 1.2.3 — BLOCKED
- 官方 SPDX: `None`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Retain actual copyright and permission text with substantial copies, including redistribution notices. No implied warranty or trademark endorsement.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/matthewwithanm/python-markdownify/1.2.3/LICENSE; HTTP 200; SHA fae8b42db142dabf03b0c5c495831a5d11b9649ead0cf0bd4ab4f52294b263be

## markitdown

### 0.1.9 — BLOCKED
- 官方 SPDX: `MIT`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Retain actual copyright and permission text with substantial copies, including redistribution notices. No implied warranty or trademark endorsement.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/microsoft/markitdown/v0.1.9/LICENSE; HTTP 200; SHA c2cfccb812fe482101a8f04597dfc5a9991a6b2748266c47ac91b6a5aae15383

## numpy

### 2.5.4 — BLOCKED
- 官方 SPDX: `BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Project BSD LICENSE captured. Attempts for LICENSES_bundled.txt and wheel license templates returned 404; this does not establish bundled absence. BLAS/LAPACK/compiler runtimes and generated wheel licenses remain unverified, no claim of actual linkage.
- Retain copyright, conditions and disclaimer in source and binary distribution materials; no author/contributor endorsement without permission.
- Actual BLAS/LAPACK and compiler-runtime (including any OpenBLAS or GCC runtime/exception if present) versions, linkage, notices and source obligations; no bundled binary acquired to substantiate membership.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- BUNDLED_NATIVE_OR_ASSET_LICENSE_CLOSURE_UNRESOLVED
- 来源: https://raw.githubusercontent.com/numpy/numpy/v2.5.4/LICENSE.txt; HTTP 200; SHA 1be1df33863f97a7bc1c4d67980bd6c69c9a6fef0a5ee76e6ad6cb91e56e8491

## onnxruntime

### 1.31.1 — BLOCKED
- 官方 SPDX: `None`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- MIT root and exact-tag ThirdPartyNotices.txt captured. Repo notice aggregate is not the exact target wheel closure or evidence that all entries are present. Per-platform native/ONNX/provider components and compiler runtimes require exact wheel comparison.
- Retain actual copyright and permission text with substantial copies, including redistribution notices. No implied warranty or trademark endorsement.
- Actual CPU/provider/runtime/vendor native membership, license versions and generated ThirdPartyNotices for every target, not just repo aggregate.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- BUNDLED_NATIVE_OR_ASSET_LICENSE_CLOSURE_UNRESOLVED
- 来源: https://raw.githubusercontent.com/microsoft/onnxruntime/v1.31.1/LICENSE; HTTP 200; SHA 2f07c72751aed99790b8a4869cf2311df85a860b22ded05fa22803587a48922c
- 来源: https://raw.githubusercontent.com/microsoft/onnxruntime/v1.31.1/ThirdPartyNotices.txt; HTTP 200; SHA 143764b952fdb1a7c69ce653bfba74a7744d6a8a573bfb73e235fba356c83de3

## openpyxl

### 3.1.5 — BLOCKED
- 官方 SPDX: `None`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Do not redistribute until precise version license, copyright chain and artifact-native notices are established.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://foss.heptapod.net/openpyxl/openpyxl/-/raw/3.1.5/LICENCE.rst; HTTP 200; SHA 0c84bb42f5d367e5ebf9fc2dde35b16141df5ee0fdc189250858bc6c5560f69e

## packaging

### 26.3 — BLOCKED
- 官方 SPDX: `Apache-2.0 OR BSD-2-Clause`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Exact-tag LICENSE plus both complete license alternatives captured; preserve choice and actual wheel notices.
- Choose and document a permitted license route for the relevant project code; do not erase differently licensed historical/vendored component notices. Apply corresponding Apache or BSD obligations.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/pypa/packaging/26.3/LICENSE; HTTP 200; SHA cad1ef5bd340d73e074ba614d26f7deaca5c7940c3d8c34852e65c4909686c48
- 来源: https://raw.githubusercontent.com/pypa/packaging/26.3/LICENSE.APACHE; HTTP 200; SHA 0d542e0c8804e39aa7f37eb00da5a762149dc682d7829451287e11b938e94594
- 来源: https://raw.githubusercontent.com/pypa/packaging/26.3/LICENSE.BSD; HTTP 200; SHA b70e7e9b742f1cc6f948b34c16aa39ffece94196364bc88ff0d2180f0028fac5

## pandas

### 3.1.1 — BLOCKED
- 官方 SPDX: `BSD-3-Clause`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Retain copyright, conditions and disclaimer in source and binary distribution materials; no author/contributor endorsement without permission.
- Compiled extensions and platform-native/compiler/runtime/transitive NumPy boundary; confirm whether bundled components exist and preserve notices.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- BUNDLED_NATIVE_OR_ASSET_LICENSE_CLOSURE_UNRESOLVED
- 来源: https://raw.githubusercontent.com/pandas-dev/pandas/v3.1.1/LICENSE; HTTP 200; SHA 9850f6b5bdef7346503065807b878deb8058b976c5c329f4c4d23bf4796ce9ae

## pdfminer-six

### 20260107 — BLOCKED
- 官方 SPDX: `MIT`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Retain actual copyright and permission text with substantial copies, including redistribution notices. No implied warranty or trademark endorsement.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/pdfminer/pdfminer.six/20260107/LICENSE; HTTP 200; SHA f01e5d699a33766b5caf4a5099f2856aba4f3f75ea1df05dc0572b34b4bea8f2

## pdfplumber

### 0.11.10 — BLOCKED
- 官方 SPDX: `None`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Retain actual copyright and permission text with substantial copies, including redistribution notices. No implied warranty or trademark endorsement.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/jsvine/pdfplumber/v0.11.10/LICENSE.txt; HTTP 200; SHA 0d48994da4d1321e395b5e64a724ed4dec63fb96b88ac5b88fc014771e690821

## pillow

### 12.3.0 — BLOCKED
- 官方 SPDX: `MIT-CMU`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Exact-tag LICENSE and about document explicitly say MIT-CMU, not ordinary MIT. Binary codecs/library notices may differ by target.
- Retain copyrights in all copies and copyright/permission notices in supporting documentation; do not use Secret Labs AB/author name in advertising or publicity without written permission.
- Potential JPEG/JPEG-turbo, zlib, libtiff, freetype, lcms2, webp, OpenJPEG and other codec/library/native runtime notices, versions and target flags; list is risk checklist, not observed actual wheel inventory.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- BUNDLED_NATIVE_OR_ASSET_LICENSE_CLOSURE_UNRESOLVED
- 来源: https://raw.githubusercontent.com/python-pillow/Pillow/12.3.0/docs/about.rst; HTTP 200; SHA cf0d9d2b1e15e5122c916b9e2188c1962ceb55f1afb1486ed8e168acb7e4200c
- 来源: https://raw.githubusercontent.com/python-pillow/Pillow/12.3.0/LICENSE; HTTP 200; SHA 15181e7363dca9aed78b79bebebc7fde7f1814b8bd311ea3b87ae8ccadfc185b

## protobuf

### 7.36.2 — BLOCKED
- 官方 SPDX: `None`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: UNKNOWN_OR_DIFFERENT_SCOPE
- BSD source license captured at protobuf v36.2 but Python package 7.36.2 to repository tag correspondence and official-repo link from exact metadata NOT established. Not an exact-version license clearance.
- Retain copyright, conditions and disclaimer in source and binary distribution materials; no author/contributor endorsement without permission.
- Native upb/other compiled components and third-party notices; establish Python-to-source-tag version mapping first.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- EXACT_VERSION_OFFICIAL_LICENSE_TEXT_OR_LINK_NOT_ESTABLISHED
- VERSION_LICENSE_REVIEW_UNRESOLVED
- BUNDLED_NATIVE_OR_ASSET_LICENSE_CLOSURE_UNRESOLVED
- 来源: https://raw.githubusercontent.com/protocolbuffers/protobuf/v36.2/LICENSE; HTTP 200; SHA 6e5e117324afd944dcf67f36cf329843bc1a92229a8cd9bb573d7a83130fea7d

## pycparser

### 3.12 — BLOCKED
- 官方 SPDX: `BSD-3-Clause`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Retain copyright, conditions and disclaimer in source and binary distribution materials; no author/contributor endorsement without permission.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/eliben/pycparser/release_v3.12/LICENSE; HTTP 200; SHA 0a9e78156ae8b96caf1b4f11ac2df424b83de29736f9e757630548a6272fdf90

## pypdfium2

### 5.15.1 — BLOCKED
- 官方 SPDX: `None`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Exact-tag README licensing section lines 810-831 plus full license alternatives captured. Generic BSD template has placeholders, not a full copyright chain. PDFium and its dependency licenses must accompany binary distributions; CC-BY-4.0 applies to docs/examples; build-specific libgcc risk is explicitly documented.
- Choose and document a permitted license route for the relevant project code; do not erase differently licensed historical/vendored component notices. Apply corresponding Apache or BSD obligations.
- PDFium build/version and BUILD_LICENSES directory; all PDFium third-party notices, platform binary provenance/attestation and any libgcc/runtime license exceptions. Do not reuse main/latest PDFium license in place of the actual build.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- BUNDLED_NATIVE_OR_ASSET_LICENSE_CLOSURE_UNRESOLVED
- GENERIC_LICENSE_TEMPLATE_IS_NOT_AUTHOR_COPYRIGHT_CHAIN
- 来源: https://raw.githubusercontent.com/pypdfium2-team/pypdfium2/5.15.1/LICENSES/BSD-3-Clause.txt; HTTP 200; SHA a6d11f0694c0137e9b02924b9d33a159f6c72f220fa4655bb2e1ea3654377d39
- 来源: https://raw.githubusercontent.com/pypdfium2-team/pypdfium2/5.15.1/README.md; HTTP 200; SHA 5ee00628f07e70f6bcdb5f8fd00b8b439e153ebc572c9734927a39515efc21e2
- 来源: https://raw.githubusercontent.com/pypdfium2-team/pypdfium2/5.15.1/LICENSES/Apache-2.0.txt; HTTP 200; SHA cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30

## python-dateutil

### 4.0.0 — BLOCKED
- 官方 SPDX: `BSD-3-Clause`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- LICENSE describes Apache-2.0 contributions and BSD alternative covering contributions/history. A legacy BSD label alone is not a complete component attribution statement.
- Choose and document a permitted license route for the relevant project code; do not erase differently licensed historical/vendored component notices. Apply corresponding Apache or BSD obligations.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/dateutil/dateutil/4.0.0/LICENSE; HTTP 200; SHA ba00f51a0d92823b5a1cde27d8b5b9d2321e67ed8da9bc163eff96d5e17e577e

## python-docx

### 1.2.0 — BLOCKED
- 官方 SPDX: `None`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Retain actual copyright and permission text with substantial copies, including redistribution notices. No implied warranty or trademark endorsement.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/python-openxml/python-docx/v1.2.0/LICENSE; HTTP 200; SHA 7652f271e46d0d533e9dc463f3b5fcbdcacf4d6a9c8d6b554d15efd0f37f6132

## python-pptx

### 1.0.2 — BLOCKED
- 官方 SPDX: `None`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Retain actual copyright and permission text with substantial copies, including redistribution notices. No implied warranty or trademark endorsement.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/scanny/python-pptx/v1.0.2/LICENSE; HTTP 200; SHA 7652f271e46d0d533e9dc463f3b5fcbdcacf4d6a9c8d6b554d15efd0f37f6132

## referencing

### 0.37.0 — BLOCKED
- 官方 SPDX: `MIT`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Retain actual copyright and permission text with substantial copies, including redistribution notices. No implied warranty or trademark endorsement.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/python-jsonschema/referencing/v0.37.0/COPYING; HTTP 200; SHA 42dcd63495f87b4eb7c7757afa379bb55a53f94afd7a5f657d9adf57236e515c

## requests

### 2.34.2 — BLOCKED
- 官方 SPDX: `None`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Provide Apache-2.0 text; preserve pertinent copyright/patent/trademark/attribution notices; mark modified files; if supplied, reproduce NOTICE attribution in a readable compliant place. Patent grant/termination applies; no trademark grant.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/psf/requests/v2.34.2/LICENSE; HTTP 200; SHA 09e8a9bcec8067104652c168685ab0931e7868f9c8284b66f5ae6edae5f1130b

## rpds-py

### 2026.9.1 — BLOCKED
- 官方 SPDX: `MIT`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Retain actual copyright and permission text with substantial copies, including redistribution notices. No implied warranty or trademark endorsement.
- Rust rpds component/dependency closure and platform binaries; capture original license/NOTICE and compiler/runtime linkage.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- BUNDLED_NATIVE_OR_ASSET_LICENSE_CLOSURE_UNRESOLVED
- 来源: https://raw.githubusercontent.com/crate-py/rpds/v2026.9.1/LICENSE; HTTP 200; SHA 314e4e91be3baa93c0fb4bccc9e4e97cd643eb839b065af921782c2175fe9909

## six

### 1.17.0 — BLOCKED
- 官方 SPDX: `None`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Retain actual copyright and permission text with substantial copies, including redistribution notices. No implied warranty or trademark endorsement.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/benjaminp/six/1.17.0/LICENSE; HTTP 200; SHA 4375ba20e2b9c6c4e7cad2940a628fd90e95cc3d50ee92aae755715d8ba1fbd0

## soupsieve

### 4.0.1 — BLOCKED
- 官方 SPDX: `MIT`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Retain actual copyright and permission text with substantial copies, including redistribution notices. No implied warranty or trademark endorsement.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/facelessuser/soupsieve/4.0.1/LICENSE.md; HTTP 200; SHA 76a0acdb98c3a63681e20b6f096699ef8cad5fb35d56eef8387e0fa71d797a9a

## typing-extensions

### 4.16.0 — BLOCKED
- 官方 SPDX: `PSF-2.0`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Exact-tag license includes PSF and historical Python agreements and 0BSD documentation-code terms; retain full license file, do not replace with bare SPDX header.
- Retain PSF license and copyright; when distributing derivative versions include a brief summary of changes; no implied PSF endorsement. Preserve any additional historical or embedded code licenses.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/python/typing_extensions/4.16.0/LICENSE; HTTP 200; SHA 3b2f81fe21d181c499c59a256c8e1968455d6689d269aa85373bfb6af41da3bf

## tzdata

### 2026.5 — BLOCKED
- 官方 SPDX: `None`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Provide Apache-2.0 text; preserve pertinent copyright/patent/trademark/attribution notices; mark modified files; if supplied, reproduce NOTICE attribution in a readable compliant place. Patent grant/termination applies; no trademark grant.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/python/tzdata/2026.5/LICENSE; HTTP 200; SHA df58f69ea88683035d720b5375bcef0cf5aeaa98a1d098d572e0992c378deb46
- 来源: https://raw.githubusercontent.com/python/tzdata/2026.5/licenses/LICENSE_APACHE; HTTP 200; SHA c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4

### 2026.6 — BLOCKED
- 官方 SPDX: `None`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Provide Apache-2.0 text; preserve pertinent copyright/patent/trademark/attribution notices; mark modified files; if supplied, reproduce NOTICE attribution in a readable compliant place. Patent grant/termination applies; no trademark grant.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/python/tzdata/2026.6/LICENSE; HTTP 200; SHA df58f69ea88683035d720b5375bcef0cf5aeaa98a1d098d572e0992c378deb46
- 来源: https://raw.githubusercontent.com/python/tzdata/2026.6/licenses/LICENSE_APACHE; HTTP 200; SHA c71d239df91726fc519c6eb72d318ec65820627232b2f796219e87dcf35d0ab4

## urllib3

### 2.8.0 — BLOCKED
- 官方 SPDX: `MIT`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Retain actual copyright and permission text with substantial copies, including redistribution notices. No implied warranty or trademark endorsement.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/urllib3/urllib3/2.8.0/LICENSE.txt; HTTP 200; SHA 130e3a64d5fdd5d096a752694634a7d9df284469de86e5732100268041e3d686

## xlsxwriter

### 3.3.1 — BLOCKED
- 官方 SPDX: `BSD-2-Clause`；旧字段按原始证据保存在 JSON，不能取代 SPDX 或 bundled 条款。
- Scope: EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND
- Retain copyright, conditions and disclaimer in source; reproduce them in documentation/materials accompanying binaries.
- No native/bundled membership established; still verify package-contained data, license files and NOTICE in acquired wheel.
- ARTIFACT_NOT_ACQUIRED: exact third-party wheel LICENSE/NOTICE/RECORD/native payload not read; version metadata/source text is not artifact-internal byte proof.
- Immutable tag commit / distribution source relationship, exact target wheel bytes/hash, original copyright and bundled notice equivalence must be established before redistribution.
- 来源: https://raw.githubusercontent.com/jmcnamara/XlsxWriter/RELEASE_3.3.1/LICENSE.txt; HTTP 200; SHA 79cd3a88b65ecd9996f4bbfb7f3adf0a75df366aa1d3bbb7fe150b9e43d5b4c7
