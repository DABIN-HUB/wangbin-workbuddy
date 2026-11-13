# wheelhouse 与后续安装计划（纯文字，未执行）

## 条件首目标：Windows AMD64 / 标准 GIL CPython 3.12

此处 41 个非撤回第三方文件可供未来**分批准阶段**取证；当前均 NOT_AUTHORIZED / ARTIFACT_NOT_ACQUIRED / actual_hash_verified=false / LICENSE_REVIEW=BLOCKED。
缺失 pypdfium2==5.15.1（全撤回）；没有获准替代版本或允许撤回的审批，不得闭包 PASS。
另有 internal solar==0.3.2 已本地静态审核 wheel（不是安装通过），document==1.2.0 双 SHA 未裁定；42第三方+2internal 尚不完整。
每文件 notice/版本文本状态/后续证据在 download-plan.json；不能因 pure-any 就免除数据资源或许可审核。

| 精确包版本 | wheel 文件名 | 官方 SHA256 | 精确官方 URL | Python/ABI/platform tags |
|---|---|---|---|---|
| attrs==26.1.0 | attrs-26.1.0-py3-none-any.whl | c647aa4a12dfbad9333ca4e71fe62ddc36f4e63b2d260a37a8b83d2f043ac309 | https://files.pythonhosted.org/packages/64/b4/17d4b0b2a2dc85a6df63d1157e028ed19f90d4cd97c36717afef2bc2f395/attrs-26.1.0-py3-none-any.whl | py3-none-any |
| beautifulsoup4==4.15.0 | beautifulsoup4-4.15.0-py3-none-any.whl | d6f88de62e1d4e38ecb1077eb9724cd0eff29d2a08ca16a401e9b9e93f117cf9 | https://files.pythonhosted.org/packages/88/c6/92fcd42f1ba33e1184263f25bfabf3d27c383410470f169e4b8163bf9c17/beautifulsoup4-4.15.0-py3-none-any.whl | py3-none-any |
| certifi==2026.10.23 | certifi-2026.10.23-py3-none-any.whl | e9b54de76e530bb6cf0ccd036787103acb58fd42ba930ea8bf948ddbaa2f61d1 | https://files.pythonhosted.org/packages/32/d1/a3652fe2c19134d0d15922177821d863cbd7e842d53a21bbe7e8e3a1b5ac/certifi-2026.10.23-py3-none-any.whl | py3-none-any |
| cffi==2.1.1 | cffi-2.1.1-cp312-cp312-win_amd64.whl | f53e442b08449d42821fa4a4fba000095af9f62742a500f978a9f557ec44339a | https://files.pythonhosted.org/packages/d9/79/615cc094e2fb508cade7de88d3b4f6c4ec2bab695c97bce9153dc65aadf5/cffi-2.1.1-cp312-cp312-win_amd64.whl | cp312-cp312-win_amd64 |
| charset-normalizer==3.5.2 | charset_normalizer-3.5.2-py3-none-any.whl | b6b751274acb69d77b3323d6b7dbaa3c7fdfc1eb829b7eb61d262f32e1af9685 | https://files.pythonhosted.org/packages/fc/ad/d07d7862a62ffa6d79d68074d14823243dd235a77c45262acbf6adeb28bf/charset_normalizer-3.5.2-py3-none-any.whl | py3-none-any |
| click==8.5.1 | click-8.5.1-py3-none-any.whl | 8bb5376d2006950386f8c6427613334a2acadc5f559cb80e638d00b4df957e37 | https://files.pythonhosted.org/packages/31/7d/164b7ffc8624fe9efb4221bf9af485d5c1e41b9ae118045d2b6dc5457d8b/click-8.5.1-py3-none-any.whl | py3-none-any |
| cobble==0.1.4 | cobble-0.1.4-py3-none-any.whl | 36c91b1655e599fd428e2b95fdd5f0da1ca2e9f1abb0bc871dec21a0e78a2b44 | https://files.pythonhosted.org/packages/d5/e1/3714a2f371985215c219c2a70953d38e3eed81ef165aed061d21de0e998b/cobble-0.1.4-py3-none-any.whl | py3-none-any |
| cryptography==50.0.2 | cryptography-50.0.2-cp311-abi3-win_amd64.whl | 7afa5a6602a9f29af1f3a2965f831bae7c9d5d597b7cbb716d41ab3b7d89879c | https://files.pythonhosted.org/packages/9a/4f/adfc442765721292fff86d314ce385d3249d22db42295c0dd057727b60f3/cryptography-50.0.2-cp311-abi3-win_amd64.whl | cp311-abi3-win_amd64 |
| defusedxml==0.7.1 | defusedxml-0.7.1-py2.py3-none-any.whl | a352e7e428770286cc899e2542b6cdaedb2b4953ff269a210103ec58f6198a61 | https://files.pythonhosted.org/packages/07/6c/aa3f2f849e01cb6a001cd8554a88d4c77c5c1a31c95bdf1cf9301e6d9ef4/defusedxml-0.7.1-py2.py3-none-any.whl | py2-none-any,py3-none-any |
| et-xmlfile==2.0.0 | et_xmlfile-2.0.0-py3-none-any.whl | 7a91720bc756843502c3b7504c77b8fe44217c85c537d85037f0f536151b2caa | https://files.pythonhosted.org/packages/c1/8b/5fe2cc11fee489817272089c4203e679c63b570a5aaeb18d852ae3cbba6a/et_xmlfile-2.0.0-py3-none-any.whl | py3-none-any |
| flatbuffers==25.12.19 | flatbuffers-25.12.19-py2.py3-none-any.whl | 7634f50c427838bb021c2d66a3d1168e9d199b0607e6329399f04846d42e20b4 | https://files.pythonhosted.org/packages/e8/2d/d2a548598be01649e2d46231d151a6c56d10b964d94043a335ae56ea2d92/flatbuffers-25.12.19-py2.py3-none-any.whl | py2-none-any,py3-none-any |
| idna==3.20 | idna-3.20-py3-none-any.whl | ab7ae7122974553370f0bdb919e1a960b2cd1bc1ef0276416d896db81c14582c | https://files.pythonhosted.org/packages/58/a2/bb081bab032533a855d44de1d56f8e8426114ff1ba5d1f07a438a0a654f8/idna-3.20-py3-none-any.whl | py3-none-any |
| jsonschema==4.26.0 | jsonschema-4.26.0-py3-none-any.whl | d489f15263b8d200f8387e64b4c3a75f06629559fb73deb8fdfb525f2dab50ce | https://files.pythonhosted.org/packages/69/90/f63fb5873511e014207a475e2bb4e8b2e570d655b00ac19a9a0ca0a385ee/jsonschema-4.26.0-py3-none-any.whl | py3-none-any |
| jsonschema-specifications==2025.9.1 | jsonschema_specifications-2025.9.1-py3-none-any.whl | 98802fee3a11ee76ecaca44429fda8a41bff98b00a0f2838151b113f210cc6fe | https://files.pythonhosted.org/packages/41/45/1a4ed80516f02155c51f51e8cedb3c1902296743db0bbc66608a0db2814f/jsonschema_specifications-2025.9.1-py3-none-any.whl | py3-none-any |
| lxml==6.1.3 | lxml-6.1.3-cp312-cp312-win_amd64.whl | 3e9a00d1c2c30936f7add097c41afc5da6556c580909104aafd382cac92a855c | https://files.pythonhosted.org/packages/3a/5b/6ed903e4e6278a020c8a6f0dbbe78030d041840a6b4a64ea441a1e414077/lxml-6.1.3-cp312-cp312-win_amd64.whl | cp312-cp312-win_amd64 |
| magika==1.0.3 | magika-1.0.3-py3-none-any.whl | 938d8e033953f2ddeb8c35dc423aa289ca116bfa7a71a778f6e77460f9025803 | https://files.pythonhosted.org/packages/93/eb/24d94db0530029649b266ec3ca8221c07f2754f56046181f13237d2518f5/magika-1.0.3-py3-none-any.whl | py3-none-any |
| mammoth==1.13.0 | mammoth-1.13.0-py2.py3-none-any.whl | dd7629fa9d0a5e82207b3f481a9dcb8308fb43f6206258e062f11121efba9991 | https://files.pythonhosted.org/packages/af/2a/47d72b27689f3c7cd1d270dd1d4699df2fe3b78b2f293b6b08f565548a45/mammoth-1.13.0-py2.py3-none-any.whl | py2-none-any,py3-none-any |
| markdownify==1.2.3 | markdownify-1.2.3-py3-none-any.whl | a189a0bedfd14009030fde5f85bb6f77c56897cb839b5c25315dd7d4e3e290ba | https://files.pythonhosted.org/packages/04/10/fa543d484e8b1199243fe20eedd02cc5af050edebce98a7293a5773df592/markdownify-1.2.3-py3-none-any.whl | py3-none-any |
| markitdown==0.1.9 | markitdown-0.1.9-py3-none-any.whl | 52f59c48bea9cf887224c56247f648d68beb7aa7af5a12d414748210c83c20ea | https://files.pythonhosted.org/packages/b3/ce/027c1e647909447fa29a5d3eb87d5e98013d49dc0b568602b129a9d06751/markitdown-0.1.9-py3-none-any.whl | py3-none-any |
| numpy==2.5.4 | numpy-2.5.4-cp312-cp312-win_amd64.whl | a7b1b6353e36a7e50de2973a38d705c88ee93adcf120673cee7f45a4a3fa223a | https://files.pythonhosted.org/packages/12/33/fefe62073dc8acfd0f2b9ed7c003af2f50aa61555e113e6db02b8f79f145/numpy-2.5.4-cp312-cp312-win_amd64.whl | cp312-cp312-win_amd64 |
| onnxruntime==1.31.1 | onnxruntime-1.31.1-cp312-cp312-win_amd64.whl | ae8a9a351efda685cc59a66226cdefaa37a126c1d66872ca23a2de9425326130 | https://files.pythonhosted.org/packages/45/b2/793b4051d8dc6acb379ead9b72050f0ffa283ca49a6904add2e218b83e2e/onnxruntime-1.31.1-cp312-cp312-win_amd64.whl | cp312-cp312-win_amd64 |
| openpyxl==3.1.5 | openpyxl-3.1.5-py2.py3-none-any.whl | 5282c12b107bffeef825f4617dc029afaf41d0ea60823bbb665ef3079dc79de2 | https://files.pythonhosted.org/packages/c0/da/977ded879c29cbd04de313843e76868e6e13408a94ed6b987245dc7c8506/openpyxl-3.1.5-py2.py3-none-any.whl | py2-none-any,py3-none-any |
| packaging==26.3 | packaging-26.3-py3-none-any.whl | d7193f7c8e4e93f444fde0262bf90af30e16fa0ad0ad44cb553c87339b23cd1c | https://files.pythonhosted.org/packages/63/34/ba1c580383c9eada3711951fef0795c80b829a078d72188184bcab9dd527/packaging-26.3-py3-none-any.whl | py3-none-any |
| pandas==3.1.1 | pandas-3.1.1-cp312-cp312-win_amd64.whl | eef35cb3f07dbc8e10e298b8a55ee4aa04d6511f27d5277f13c3df45d3bbef5c | https://files.pythonhosted.org/packages/c8/35/54c22df9e6bdb0fa001da2b8855f997addafd9575f14f25c166a8ef96b6e/pandas-3.1.1-cp312-cp312-win_amd64.whl | cp312-cp312-win_amd64 |
| pdfminer-six==20260107 | pdfminer_six-20260107-py3-none-any.whl | 366585ba97e80dffa8f00cebe303d2f381884d8637af4ce422f1df3ef38111a9 | https://files.pythonhosted.org/packages/20/8b/28c4eaec9d6b036a52cb44720408f26b1a143ca9bce76cc19e8f5de00ab4/pdfminer_six-20260107-py3-none-any.whl | py3-none-any |
| pdfplumber==0.11.10 | pdfplumber-0.11.10-py3-none-any.whl | 7741ea81bf165b474b153e6789d10d18e06b6ddcf3ec84289c3ef2fed6802580 | https://files.pythonhosted.org/packages/a2/9a/07d658e1e7fad860f1c541ab941348125dbdab773be3a0afaf32361866c7/pdfplumber-0.11.10-py3-none-any.whl | py3-none-any |
| pillow==12.3.0 | pillow-12.3.0-cp312-cp312-win_amd64.whl | a2b55dd6b2a4c4b7d87ffa56bdb33fdc5fdb9a462173861a7bc097f17d91cb09 | https://files.pythonhosted.org/packages/45/89/da2f7971a317f83d807fdd4065c0af40208e59e692cc43d315a71a0e96d1/pillow-12.3.0-cp312-cp312-win_amd64.whl | cp312-cp312-win_amd64 |
| protobuf==7.36.2 | protobuf-7.36.2-py3-none-any.whl | bdb3a345d48db958e6ce1f18e508beb0cc981d64f24088427549c866cd039f1e | https://files.pythonhosted.org/packages/e4/04/d52c7016b04b6c5108f26691f9d33ec82a9b65d041f1a9c771137693d618/protobuf-7.36.2-py3-none-any.whl | py3-none-any |
| pycparser==3.12 | pycparser-3.12-py3-none-any.whl | a076f3f489b39b43ed13563a1dafe42447445bec2e294154ec5c57fcdda4c85e | https://files.pythonhosted.org/packages/b6/ae/315bbeee126a769cbde43cf4908acb4b40408d8bf8bbf334dd7368d8dadf/pycparser-3.12-py3-none-any.whl | py3-none-any |
| python-dateutil==4.0.0 | python_dateutil-4.0.0-py3-none-any.whl | a5e246f79eb80475e691bf93862cead98decd8a498cf53ba0516fcdc0f50dc1c | https://files.pythonhosted.org/packages/2f/a9/52b89563d154433d79b51ed1eb4842bf7334cb2696891a7fe135618853d7/python_dateutil-4.0.0-py3-none-any.whl | py3-none-any |
| python-docx==1.2.0 | python_docx-1.2.0-py3-none-any.whl | 3fd478f3250fbbbfd3b94fe1e985955737c145627498896a8a6bf81f4baf66c7 | https://files.pythonhosted.org/packages/d0/00/1e03a4989fa5795da308cd774f05b704ace555a70f9bf9d3be057b680bcf/python_docx-1.2.0-py3-none-any.whl | py3-none-any |
| python-pptx==1.0.2 | python_pptx-1.0.2-py3-none-any.whl | 160838e0b8565a8b1f67947675886e9fea18aa5e795db7ae531606d68e785cba | https://files.pythonhosted.org/packages/d9/4f/00be2196329ebbff56ce564aa94efb0fbc828d00de250b1980de1a34ab49/python_pptx-1.0.2-py3-none-any.whl | py3-none-any |
| referencing==0.37.0 | referencing-0.37.0-py3-none-any.whl | 381329a9f99628c9069361716891d34ad94af76e461dcb0335825aecc7692231 | https://files.pythonhosted.org/packages/2c/58/ca301544e1fa93ed4f80d724bf5b194f6e4b945841c5bfd555878eea9fcb/referencing-0.37.0-py3-none-any.whl | py3-none-any |
| requests==2.34.2 | requests-2.34.2-py3-none-any.whl | 2a0d60c172f83ac6ab31e4554906c0f3b3588d37b5cb939b1c061f4907e278e0 | https://files.pythonhosted.org/packages/a0/f4/c67b0b3f1b9245e8d266f0f112c500d50e5b4e83cb6f3b71b6528104182a/requests-2.34.2-py3-none-any.whl | py3-none-any |
| rpds-py==2026.9.1 | rpds_py-2026.9.1-cp312-cp312-win_amd64.whl | 5ce8943f79c2210f7abcc28e86367b03b28d95027fd01c46d2472373ae70c86f | https://files.pythonhosted.org/packages/1c/84/1700cc748d0eaa747486e4e82882d2575224e6e9a3148df583058850c629/rpds_py-2026.9.1-cp312-cp312-win_amd64.whl | cp312-cp312-win_amd64 |
| six==1.17.0 | six-1.17.0-py2.py3-none-any.whl | 4721f391ed90541fddacab5acf947aa0d3dc7d27b2e1e8eda2be8970586c3274 | https://files.pythonhosted.org/packages/b7/ce/149a00dd41f10bc29e5921b496af8b574d8413afcd5e30dfa0ed46c2cc5e/six-1.17.0-py2.py3-none-any.whl | py2-none-any,py3-none-any |
| soupsieve==4.0.1 | soupsieve-4.0.1-py3-none-any.whl | 2e68cf7dd5a0f29d81f9d485275ccf294e6475f615e211895d91cb81f8614f04 | https://files.pythonhosted.org/packages/2c/5c/4f68370847b561a389dd9a2d7eb3d19fd8cbb8acbae543a0c6b8d0d9700b/soupsieve-4.0.1-py3-none-any.whl | py3-none-any |
| typing-extensions==4.16.0 | typing_extensions-4.16.0-py3-none-any.whl | 481caa481374e813c1b176ada14e97f1f67a4539ce9cfeb3f350d78d6370c2e8 | https://files.pythonhosted.org/packages/49/d3/b8441a820a491ddfc024b0b0cf0393375b75ea13866d9c66727e54c2fc80/typing_extensions-4.16.0-py3-none-any.whl | py3-none-any |
| tzdata==2026.5 | tzdata-2026.5-py2.py3-none-any.whl | b683bd1b6659ddcd810ff02ad09ba821d4bf1065072805063eb35c49617905ac | https://files.pythonhosted.org/packages/94/21/1e5995a1c920cce14e4bffae20c665ec10e7ed03ab25e006cd741092b718/tzdata-2026.5-py2.py3-none-any.whl | py2-none-any,py3-none-any |
| urllib3==2.8.0 | urllib3-2.8.0-py3-none-any.whl | 0cf3cae568d36aa9576b28dfb35f11328f1cb974ca7647d9475ebb86c75ac6e3 | https://files.pythonhosted.org/packages/92/9d/c4e665119135114480843e7ab388fa94d8480650450e6f8e26b70d323a4c/urllib3-2.8.0-py3-none-any.whl | py3-none-any |
| xlsxwriter==3.3.1 | xlsxwriter-3.3.1-py3-none-any.whl | 8e2c89e59d733fe59e112317218c64fbbc276d90a8c144ebd6f7fa15e7ab184a | https://files.pythonhosted.org/packages/88/eb/1e6af9959a567901a7e7c7cef2e75883e487df223ed67f9a8977ff863bd8/xlsxwriter-3.3.1-py3-none-any.whl | py3-none-any |

## 十二目标去重与受控下载提案

115 唯一身份严格以 filename + SHA256 + URL 去重；34 pure、81 platform、486分配、18缺口。
全部目标所需 file_ids 与具体 gaps 在 download-plan.json.targets；全115项URL/hash/tags/目标/逐项notice条件在 files。
setuptools 84.1.0 / wheel 0.48.0 仅 backend 来源研究，既非 runtime42，也不在首目标41下载集合；动态 backend 需求未运行未知。

1. 人工先确认正式 runtime/patch/ABI/OS，并批准精确 URL/hash 列表、保存目录、体积与网络边界；许可研究不等于取得或再分发授权。
2. 若只批准首目标41件证据下载，仍标识为不完整取证批次，不进行安装；拒绝 yanked，拒绝 hash/版本/URL 不一致，拒绝静默替代。
3. 独立审批解决 pypdfium2 pin、document 双构件和三项文本缺口；任何版本调整必须新建候选图与独立复核，不能改原合同来填洞。
4. 审批后每件实际文件先计算完整 SHA256，再核安全路径/ZIP唯一成员/CRC/RECORD/元数据/各层 LICENSE/NOTICE/native来源，建立 acquired 与 actual_hash_verified 的真实回执。
5. 未通过的文件隔离，不能进 approved；hash一致仅证明身份，不等于来源签名证明或法律批准。

## 未来目录（本轮没有创建 wheelhouse）

- wheelhouse/proposed/<target>/ 仅候选 manifest，不放未获准二进制。
- wheelhouse/quarantine/<filename+sha>/ 保存获准下载待核文件与来源/时间回执。
- wheelhouse/approved/<target>/ 只收完成各门禁的不可变文件，纯Python可内容寻址复用，target manifest 显式映射。
- wheelhouse/notices/<filename+sha>/ 保留实际构件版权、许可、NOTICE 与对应源码/链接义务。
- wheelhouse/baseline/<engine-sha>/ 十二外置必需资源；optional-demo 独立审批与 SYNTHETIC 标识。

## 隔离离线安装方案（禁止本轮执行；不含可执行联网安装代码）

获得完整构件闭包/许可/资源及独立批准后，使用一个全新专用目录与已确认绝对解释器；不覆盖 DEV、全局或 WorkBuddy managed venv。
清除开发 PYTHONPATH、禁用用户 site；安装只从批准 wheelhouse，禁索引/联网/隐式依赖补装与构建，要求每项严格版本/hash约束。
预先验证全部构件与资源后才安装；失败立即停止，保留命令/stdout/stderr/退出码/树级清理回执，不把缺件错误改成跳过。
隔离验证须实际进行 CLI 状态/已授权非敏感格式最小用例/错误退出码/输出重新打开；本轮只形成计划，不调用 Connector init/auth/status。

## WorkBuddy 与最小后续整改（另授权）

仅在真实托管解释器与普通 Skill Bash 绑定分别观测后才判定运行目标。Connector 仍 pin solar 0.3.1；未来只在确认公开不可变 source+hash约束路径、部署安装与回滚后，最小修改 cli.json 安装声明至获准0.3.2并同步关联metadata/文档。
不修改 Skill、不假设 file:/// 是可公开来源、不把手动sidecar校验冒充安装器 hash enforcement。
先 Connector 后独立 Skill 的安装/卸载/实际用例验证均需新授权与正式入口权利；若无私测入口则阻断，不造 preview 或要求聊天交凭据。
本轮不得模型/CH08/Word/PDF/发布/Phase E-F-G。

机器计划：`.runtime/solar-pv/SOLAR-PV-R2-DEPENDENCY-SOURCE-APPROVAL-01/candidate/download-plan.json` (251507 B, SHA-256 `4ac8f6281f24ed69ff0e64fd974dabc8efb9d21fa6e79a271d95e2502a0691bd`)
