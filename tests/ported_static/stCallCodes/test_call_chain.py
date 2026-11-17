"""
Chains of CALL / CALLCODE / DELEGATECALL / STATICCALL: where each level's
storage writes land, and what context the innermost code observes.

Ported from:
state_tests/stCallCodes/callcallcall_000Filler.json
state_tests/stCallCodes/callcallcallcode_001Filler.json
state_tests/stCallCodes/callcallcodecall_010Filler.json
state_tests/stCallCodes/callcallcodecallcode_011Filler.json
state_tests/stCallCodes/callcodecallcall_100Filler.json
state_tests/stCallCodes/callcodecallcallcode_101Filler.json
state_tests/stCallCodes/callcodecallcodecall_110Filler.json
state_tests/stCallCodes/callcodecallcodecallcode_111Filler.json
state_tests/stCallDelegateCodesHomestead/callcallcallcode_001Filler.json
state_tests/stCallDelegateCodesHomestead/callcallcodecall_010Filler.json
state_tests/stCallDelegateCodesHomestead/callcallcodecallcode_011Filler.json
state_tests/stCallDelegateCodesHomestead/callcodecallcall_100Filler.json
state_tests/stCallDelegateCodesHomestead/callcodecallcallcode_101Filler.json
state_tests/stCallDelegateCodesHomestead/callcodecallcodecall_110Filler.json
state_tests/stCallDelegateCodesHomestead/callcodecallcodecallcode_111Filler.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcallcode_001Filler.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecall_010Filler.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecallcode_011Filler.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcall_100Filler.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcallcode_101Filler.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecall_110Filler.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecallcode_111Filler.json
state_tests/stCallCodes/callcall_00Filler.json
state_tests/stCallCodes/callcallcode_01Filler.json
state_tests/stCallCodes/callcodecall_10Filler.json
state_tests/stCallCodes/callcodecallcode_11Filler.json
state_tests/stCallDelegateCodesHomestead/callcallcode_01Filler.json
state_tests/stCallDelegateCodesHomestead/callcodecall_10Filler.json
state_tests/stCallDelegateCodesHomestead/callcodecallcode_11Filler.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcode_01Filler.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecall_10Filler.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcode_11Filler.json
state_tests/stCallCodes/callcallcall_ABCB_RECURSIVEFiller.json
state_tests/stCallCodes/callcallcallcode_ABCB_RECURSIVEFiller.json
state_tests/stCallCodes/callcallcodecall_ABCB_RECURSIVEFiller.json
state_tests/stCallCodes/callcallcodecallcode_ABCB_RECURSIVEFiller.json
state_tests/stCallCodes/callcodecallcall_ABCB_RECURSIVEFiller.json
state_tests/stCallCodes/callcodecallcallcode_ABCB_RECURSIVEFiller.json
state_tests/stCallCodes/callcodecallcodecall_ABCB_RECURSIVEFiller.json
state_tests/stCallCodes/callcodecallcodecallcode_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesHomestead/callcallcallcode_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesHomestead/callcallcodecall_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesHomestead/callcallcodecallcode_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcall_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcallcode_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcodecall_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcodecallcode_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcallcode_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecall_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecallcode_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcall_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcallcode_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecall_ABCB_RECURSIVEFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecallcode_ABCB_RECURSIVEFiller.json
state_tests/stCallCodes/callcallcall_000_SuicideEndFiller.json
state_tests/stCallCodes/callcallcallcode_001_SuicideEndFiller.json
state_tests/stCallCodes/callcallcodecall_010_SuicideEndFiller.json
state_tests/stCallCodes/callcallcodecallcode_011_SuicideEndFiller.json
state_tests/stCallCodes/callcodecallcall_100_SuicideEndFiller.json
state_tests/stCallCodes/callcodecallcallcode_101_SuicideEndFiller.json
state_tests/stCallCodes/callcodecallcodecall_110_SuicideEndFiller.json
state_tests/stCallCodes/callcodecallcodecallcode_111_SuicideEndFiller.json
state_tests/stCallDelegateCodesHomestead/callcallcallcode_001_SuicideEndFiller.json
state_tests/stCallDelegateCodesHomestead/callcallcodecall_010_SuicideEndFiller.json
state_tests/stCallDelegateCodesHomestead/callcallcodecallcode_011_SuicideEndFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcall_100_SuicideEndFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcallcode_101_SuicideEndFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcodecall_110_SuicideEndFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcodecallcode_111_SuicideEndFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcallcode_001_SuicideEndFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecall_010_SuicideEndFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecallcode_011_SuicideEndFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcall_100_SuicideEndFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcallcode_101_SuicideEndFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecall_110_SuicideEndFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecallcode_111_SuicideEndFiller.json
state_tests/stCallCodes/callcall_00_SuicideEndFiller.json
state_tests/stCallCodes/callcallcode_01_SuicideEndFiller.json
state_tests/stCallCodes/callcodecall_10_SuicideEndFiller.json
state_tests/stCallCodes/callcodecallcode_11_SuicideEndFiller.json
state_tests/stCallDelegateCodesHomestead/callcallcode_01_SuicideEndFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecall_10_SuicideEndFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcode_11_SuicideEndFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcode_01_SuicideEndFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecall_10_SuicideEndFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcode_11_SuicideEndFiller.json
state_tests/stCallCodes/callcallcall_000_SuicideMiddleFiller.json
state_tests/stCallCodes/callcallcallcode_001_SuicideMiddleFiller.json
state_tests/stCallCodes/callcallcodecall_010_SuicideMiddleFiller.json
state_tests/stCallCodes/callcallcodecallcode_011_SuicideMiddleFiller.json
state_tests/stCallCodes/callcodecallcall_100_SuicideMiddleFiller.json
state_tests/stCallCodes/callcodecallcallcode_101_SuicideMiddleFiller.json
state_tests/stCallCodes/callcodecallcodecall_110_SuicideMiddleFiller.json
state_tests/stCallCodes/callcodecallcodecallcode_111_SuicideMiddleFiller.json
state_tests/stCallDelegateCodesHomestead/callcallcallcode_001_SuicideMiddleFiller.json
state_tests/stCallDelegateCodesHomestead/callcallcodecall_010_SuicideMiddleFiller.json
state_tests/stCallDelegateCodesHomestead/callcallcodecallcode_011_SuicideMiddleFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcall_100_SuicideMiddleFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcallcode_101_SuicideMiddleFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcodecall_110_SuicideMiddleFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcodecallcode_111_SuicideMiddleFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcallcode_001_SuicideMiddleFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecall_010_SuicideMiddleFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecallcode_011_SuicideMiddleFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcall_100_SuicideMiddleFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcallcode_101_SuicideMiddleFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecall_110_SuicideMiddleFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecallcode_111_SuicideMiddleFiller.json
state_tests/stCallCodes/callcallcall_000_OOGEFiller.json
state_tests/stCallCodes/callcallcallcode_001_OOGEFiller.json
state_tests/stCallCodes/callcallcodecall_010_OOGEFiller.json
state_tests/stCallCodes/callcallcodecallcode_011_OOGEFiller.json
state_tests/stCallCodes/callcodecallcall_100_OOGEFiller.json
state_tests/stCallCodes/callcodecallcallcode_101_OOGEFiller.json
state_tests/stCallCodes/callcodecallcodecall_110_OOGEFiller.json
state_tests/stCallCodes/callcodecallcodecallcode_111_OOGEFiller.json
state_tests/stCallDelegateCodesHomestead/callcallcallcode_001_OOGEFiller.json
state_tests/stCallDelegateCodesHomestead/callcallcodecall_010_OOGEFiller.json
state_tests/stCallDelegateCodesHomestead/callcallcodecallcode_011_OOGEFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcall_100_OOGEFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcallcode_101_OOGEFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcodecall_110_OOGEFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcodecallcode_111_OOGEFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcallcode_001_OOGEFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecall_010_OOGEFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecallcode_011_OOGEFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcall_100_OOGEFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcallcode_101_OOGEFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecall_110_OOGEFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecallcode_111_OOGEFiller.json
state_tests/stCallCodes/callcall_00_OOGEFiller.json
state_tests/stCallCodes/callcallcode_01_OOGEFiller.json
state_tests/stCallCodes/callcodecall_10_OOGEFiller.json
state_tests/stCallCodes/callcodecallcode_11_OOGEFiller.json
state_tests/stCallDelegateCodesHomestead/callcallcode_01_OOGEFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecall_10_OOGEFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcode_11_OOGEFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcode_01_OOGEFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecall_10_OOGEFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcode_11_OOGEFiller.json
state_tests/stCallCodes/callcall_00_OOGE_valueTransferFiller.json
state_tests/stCallCodes/callcallcall_000_OOGMBeforeFiller.json
state_tests/stCallCodes/callcallcallcode_001_OOGMBeforeFiller.json
state_tests/stCallCodes/callcallcodecall_010_OOGMBeforeFiller.json
state_tests/stCallCodes/callcallcodecallcode_011_OOGMBeforeFiller.json
state_tests/stCallCodes/callcodecallcall_100_OOGMBeforeFiller.json
state_tests/stCallCodes/callcodecallcallcode_101_OOGMBeforeFiller.json
state_tests/stCallCodes/callcodecallcodecall_110_OOGMBeforeFiller.json
state_tests/stCallCodes/callcodecallcodecallcode_111_OOGMBeforeFiller.json
state_tests/stCallDelegateCodesHomestead/callcallcallcode_001_OOGMBeforeFiller.json
state_tests/stCallDelegateCodesHomestead/callcallcodecall_010_OOGMBeforeFiller.json
state_tests/stCallDelegateCodesHomestead/callcallcodecallcode_011_OOGMBeforeFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcall_100_OOGMBeforeFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcallcode_101_OOGMBeforeFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcodecall_110_OOGMBeforeFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcodecallcode_111_OOGMBeforeFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcallcode_001_OOGMBeforeFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecall_010_OOGMBeforeFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecallcode_011_OOGMBeforeFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcall_100_OOGMBeforeFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcallcode_101_OOGMBeforeFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecall_110_OOGMBeforeFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecallcode_111_OOGMBeforeFiller.json
state_tests/stCallCodes/callcallcall_000_OOGMAfterFiller.json
state_tests/stCallCodes/callcallcallcode_001_OOGMAfterFiller.json
state_tests/stCallCodes/callcallcodecall_010_OOGMAfterFiller.json
state_tests/stCallCodes/callcallcodecallcode_011_OOGMAfterFiller.json
state_tests/stCallCodes/callcodecallcall_100_OOGMAfterFiller.json
state_tests/stCallCodes/callcodecallcallcode_101_OOGMAfterFiller.json
state_tests/stCallCodes/callcodecallcodecall_110_OOGMAfterFiller.json
state_tests/stCallCodes/callcodecallcodecallcode_111_OOGMAfterFiller.json
state_tests/stCallDelegateCodesHomestead/callcallcallcode_001_OOGMAfterFiller.json
state_tests/stCallDelegateCodesHomestead/callcallcodecall_010_OOGMAfterFiller.json
state_tests/stCallDelegateCodesHomestead/callcallcodecallcode_011_OOGMAfterFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcall_100_OOGMAfterFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcallcode_101_OOGMAfterFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcodecall_110_OOGMAfterFiller.json
state_tests/stCallDelegateCodesHomestead/callcodecallcodecallcode_111_OOGMAfterFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcallcode_001_OOGMAfterFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecall_010_OOGMAfterFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecallcode_011_OOGMAfterFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcall_100_OOGMAfterFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcallcode_101_OOGMAfterFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecall_110_OOGMAfterFiller.json
state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecallcode_111_OOGMAfterFiller.json
state_tests/stStaticCall/static_callcall_00Filler.json
state_tests/stStaticCall/static_callcallcall_000Filler.json
state_tests/stStaticCall/static_callcallcallcode_001Filler.json
state_tests/stStaticCall/static_callcallcallcode_001_2Filler.json
state_tests/stStaticCall/static_callcallcode_01_2Filler.json
state_tests/stStaticCall/static_callcallcodecall_010Filler.json
state_tests/stStaticCall/static_callcallcodecall_010_2Filler.json
state_tests/stStaticCall/static_callcallcodecallcode_011Filler.json
state_tests/stStaticCall/static_callcallcodecallcode_011_2Filler.json
state_tests/stStaticCall/static_callcodecall_10Filler.json
state_tests/stStaticCall/static_callcodecall_10_2Filler.json
state_tests/stStaticCall/static_callcodecallcall_100Filler.json
state_tests/stStaticCall/static_callcodecallcall_100_2Filler.json
state_tests/stStaticCall/static_callcodecallcallcode_101Filler.json
state_tests/stStaticCall/static_callcodecallcallcode_101_2Filler.json
state_tests/stStaticCall/static_callcodecallcodecall_1102Filler.json
state_tests/stStaticCall/static_callcodecallcodecall_110Filler.json
state_tests/stStaticCall/static_callcodecallcodecall_110_2Filler.json
state_tests/stStaticCall/static_calldelcode_01Filler.json
state_tests/stStaticCall/static_callcall_00_OOGEFiller.json
state_tests/stStaticCall/static_callcall_00_OOGE_1Filler.json
state_tests/stStaticCall/static_callcall_00_OOGE_2Filler.json
state_tests/stStaticCall/static_callcallcall_000_OOGEFiller.json
state_tests/stStaticCall/static_callcallcallcode_001_OOGEFiller.json
state_tests/stStaticCall/static_callcallcallcode_001_OOGE_2Filler.json
state_tests/stStaticCall/static_callcallcode_01_OOGE_2Filler.json
state_tests/stStaticCall/static_callcallcodecall_010_OOGEFiller.json
state_tests/stStaticCall/static_callcallcodecall_010_OOGE_2Filler.json
state_tests/stStaticCall/static_callcallcodecallcode_011_OOGEFiller.json
state_tests/stStaticCall/static_callcallcodecallcode_011_OOGE_2Filler.json
state_tests/stStaticCall/static_callcodecall_10_OOGEFiller.json
state_tests/stStaticCall/static_callcodecall_10_OOGE_2Filler.json
state_tests/stStaticCall/static_callcodecallcall_100_OOGE2Filler.json
state_tests/stStaticCall/static_callcodecallcall_100_OOGEFiller.json
state_tests/stStaticCall/static_callcodecallcallcode_101_OOGEFiller.json
state_tests/stStaticCall/static_callcodecallcallcode_101_OOGE_2Filler.json
state_tests/stStaticCall/static_callcodecallcodecall_110_OOGE2Filler.json
state_tests/stStaticCall/static_callcodecallcodecall_110_OOGEFiller.json
state_tests/stStaticCall/static_calldelcode_01_OOGEFiller.json
state_tests/stStaticCall/static_callcallcall_000_OOGMBeforeFiller.json
state_tests/stStaticCall/static_callcallcallcode_001_OOGMBefore2Filler.json
state_tests/stStaticCall/static_callcallcallcode_001_OOGMBeforeFiller.json
state_tests/stStaticCall/static_callcallcodecall_010_OOGMBefore2Filler.json
state_tests/stStaticCall/static_callcallcodecall_010_OOGMBeforeFiller.json
state_tests/stStaticCall/static_callcallcodecallcode_011_OOGMBefore2Filler.json
state_tests/stStaticCall/static_callcallcodecallcode_011_OOGMBeforeFiller.json
state_tests/stStaticCall/static_callcodecallcall_100_OOGMBefore2Filler.json
state_tests/stStaticCall/static_callcodecallcall_100_OOGMBeforeFiller.json
state_tests/stStaticCall/static_callcodecallcallcode_101_OOGMBefore2Filler.json
state_tests/stStaticCall/static_callcodecallcallcode_101_OOGMBeforeFiller.json
state_tests/stStaticCall/static_callcodecallcodecall_110_OOGMBefore2Filler.json
state_tests/stStaticCall/static_callcodecallcodecall_110_OOGMBeforeFiller.json
state_tests/stStaticCall/static_callcallcall_000_OOGMAfter2Filler.json
state_tests/stStaticCall/static_callcallcall_000_OOGMAfterFiller.json
state_tests/stStaticCall/static_callcallcallcode_001_OOGMAfter2Filler.json
state_tests/stStaticCall/static_callcallcallcode_001_OOGMAfterFiller.json
state_tests/stStaticCall/static_callcallcallcode_001_OOGMAfter_2Filler.json
state_tests/stStaticCall/static_callcallcallcode_001_OOGMAfter_3Filler.json
state_tests/stStaticCall/static_callcallcodecall_010_OOGMAfter2Filler.json
state_tests/stStaticCall/static_callcallcodecall_010_OOGMAfterFiller.json
state_tests/stStaticCall/static_callcallcodecall_010_OOGMAfter_2Filler.json
state_tests/stStaticCall/static_callcallcodecall_010_OOGMAfter_3Filler.json
state_tests/stStaticCall/static_callcallcodecallcode_011_OOGMAfter2Filler.json
state_tests/stStaticCall/static_callcallcodecallcode_011_OOGMAfterFiller.json
state_tests/stStaticCall/static_callcallcodecallcode_011_OOGMAfter_1Filler.json
state_tests/stStaticCall/static_callcallcodecallcode_011_OOGMAfter_2Filler.json
state_tests/stStaticCall/static_callcodecallcall_100_OOGMAfter2Filler.json
state_tests/stStaticCall/static_callcodecallcall_100_OOGMAfterFiller.json
state_tests/stStaticCall/static_callcodecallcall_100_OOGMAfter_2Filler.json
state_tests/stStaticCall/static_callcodecallcall_100_OOGMAfter_3Filler.json
state_tests/stStaticCall/static_callcodecallcallcode_101_OOGMAfter2Filler.json
state_tests/stStaticCall/static_callcodecallcallcode_101_OOGMAfterFiller.json
state_tests/stStaticCall/static_callcodecallcallcode_101_OOGMAfter_1Filler.json
state_tests/stStaticCall/static_callcodecallcallcode_101_OOGMAfter_3Filler.json
state_tests/stStaticCall/static_callcodecallcodecall_110_OOGMAfter2Filler.json
state_tests/stStaticCall/static_callcodecallcodecall_110_OOGMAfterFiller.json
state_tests/stStaticCall/static_callcodecallcodecall_110_OOGMAfter_2Filler.json
state_tests/stStaticCall/static_callcodecallcodecall_110_OOGMAfter_3Filler.json
state_tests/stStaticCall/static_callcall_00_SuicideEndFiller.json
state_tests/stStaticCall/static_callcallcall_000_SuicideEndFiller.json
state_tests/stStaticCall/static_callcallcallcode_001_SuicideEnd2Filler.json
state_tests/stStaticCall/static_callcallcallcode_001_SuicideEndFiller.json
state_tests/stStaticCall/static_callcallcode_01_SuicideEnd2Filler.json
state_tests/stStaticCall/static_callcallcode_01_SuicideEndFiller.json
state_tests/stStaticCall/static_callcallcodecall_010_SuicideEnd2Filler.json
state_tests/stStaticCall/static_callcallcodecall_010_SuicideEndFiller.json
state_tests/stStaticCall/static_callcallcodecallcode_011_SuicideEnd2Filler.json
state_tests/stStaticCall/static_callcallcodecallcode_011_SuicideEndFiller.json
state_tests/stStaticCall/static_callcodecall_10_SuicideEnd2Filler.json
state_tests/stStaticCall/static_callcodecall_10_SuicideEndFiller.json
state_tests/stStaticCall/static_callcodecallcall_100_SuicideEnd2Filler.json
state_tests/stStaticCall/static_callcodecallcall_100_SuicideEndFiller.json
state_tests/stStaticCall/static_callcodecallcallcode_101_SuicideEnd2Filler.json
state_tests/stStaticCall/static_callcodecallcallcode_101_SuicideEndFiller.json
state_tests/stStaticCall/static_callcodecallcodecall_110_SuicideEnd2Filler.json
state_tests/stStaticCall/static_callcodecallcodecall_110_SuicideEndFiller.json
state_tests/stStaticCall/static_callcodecallcodecallcode_111_SuicideEndFiller.json
state_tests/stStaticCall/static_callcallcall_000_SuicideMiddleFiller.json
state_tests/stStaticCall/static_callcallcallcode_001_SuicideMiddle2Filler.json
state_tests/stStaticCall/static_callcallcallcode_001_SuicideMiddleFiller.json
state_tests/stStaticCall/static_callcallcodecall_010_SuicideMiddle2Filler.json
state_tests/stStaticCall/static_callcallcodecall_010_SuicideMiddleFiller.json
state_tests/stStaticCall/static_callcallcodecallcode_011_SuicideMiddle2Filler.json
state_tests/stStaticCall/static_callcallcodecallcode_011_SuicideMiddleFiller.json
state_tests/stStaticCall/static_callcodecallcall_100_SuicideMiddle2Filler.json
state_tests/stStaticCall/static_callcodecallcall_100_SuicideMiddleFiller.json
state_tests/stStaticCall/static_callcodecallcallcode_101_SuicideMiddle2Filler.json
state_tests/stStaticCall/static_callcodecallcallcode_101_SuicideMiddleFiller.json
state_tests/stStaticCall/static_callcodecallcodecall_110_SuicideMiddle2Filler.json
state_tests/stStaticCall/static_callcodecallcodecall_110_SuicideMiddleFiller.json
state_tests/stStaticCall/static_callcallcall_ABCB_RECURSIVEFiller.json
state_tests/stStaticCall/static_callcallcallcode_ABCB_RECURSIVE2Filler.json
state_tests/stStaticCall/static_callcallcallcode_ABCB_RECURSIVEFiller.json
state_tests/stStaticCall/static_callcallcodecall_ABCB_RECURSIVE2Filler.json
state_tests/stStaticCall/static_callcallcodecall_ABCB_RECURSIVEFiller.json
state_tests/stStaticCall/static_callcallcodecallcode_ABCB_RECURSIVE2Filler.json
state_tests/stStaticCall/static_callcallcodecallcode_ABCB_RECURSIVEFiller.json
state_tests/stStaticCall/static_callcodecallcall_ABCB_RECURSIVE2Filler.json
state_tests/stStaticCall/static_callcodecallcall_ABCB_RECURSIVEFiller.json
state_tests/stStaticCall/static_callcodecallcallcode_ABCB_RECURSIVE2Filler.json
state_tests/stStaticCall/static_callcodecallcallcode_ABCB_RECURSIVEFiller.json
state_tests/stStaticCall/static_callcodecallcodecall_ABCB_RECURSIVE2Filler.json
state_tests/stStaticCall/static_callcodecallcodecall_ABCB_RECURSIVEFiller.json

@manually-enhanced: Do not overwrite. The fillers are one chain test copied
into three directories, each substituting a different pair of call opcodes,
so they collapse to one test per chain depth parametrized on every chain of
CALL, CALLCODE and DELEGATECALL. The Homestead copies added CALLER stores to
some intermediate levels and moved the innermost CALLVALUE store between
slots 5, 6 and 7; every intermediate level now stores CALLER and the innermost
code stores CALLVALUE in slot 7. The post state is derived from the opcodes:
CALL moves the context to the callee, CALLCODE keeps the caller's account
but makes it the CALLER, and DELEGATECALL keeps the caller's whole context.

In the recursive A -> B -> C -> B chains, the fillers recursed until the
gas ran out (about 132 rounds, of which only the first re-entry decided the
outcome). The recursion is now bounded by a round count passed down as
calldata, together with B's address, which C would otherwise have to embed
while B embeds C's.

In the SELFDESTRUCT chains the beneficiary is passed down as calldata too,
and the destroyed account is whichever account the self-destructing frame
runs as. Before EIP-6780 it is deleted; from Cancun on it keeps its code
and storage and only its balance moves, unless it is its own beneficiary.

In the out-of-gas chains one frame (the innermost, or a calling frame
before or after its own call) runs out of gas expanding memory to 3 MB for a
KECCAK256, which takes about 19.2M gas. Only the call into that frame
is given bounded gas, so its caller keeps enough to record the failure.

The stStaticCall fillers are the same chains with STATICCALL in them, and
copies of each with CALLCODE or DELEGATECALL swapped in. Their frames below
a STATICCALL only wrote memory, so their posts asserted almost nothing (the
ABCB_RECURSIVE ones only zeros), and they embedded each other's addresses.
They collapse to chains of all four opcodes with at least one STATICCALL.
Every frame returns how many frames below it returned, plus the innermost
frame's CALLER, CALLVALUE and ADDRESS, so a static frame's outcome reaches
the top level, which stores it and then sets a done flag. Non-static
frames also store their call's success, as above. A write, a CALL with value or a SELFDESTRUCT in a static
frame halts it. A SELFDESTRUCT in a non-static frame (any frame above the
first STATICCALL) succeeds and moves the balance to a fresh beneficiary.
"""

from dataclasses import dataclass
from itertools import product

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytecode,
    Fork,
    Op,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Cancun

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

CALL_OPCODES = {
    "call": Op.CALL,
    "callcode": Op.CALLCODE,
    "delegatecall": Op.DELEGATECALL,
}
CONTRACT_BALANCE = 10**18
GAS_PRICE = 10
WINDOW = 64
CALLER_SLOT = 4
CALLVALUE_SLOT = 7
ROUNDS_OFFSET = 32
OUT_OF_GAS_MEMORY = Op.SHA3(offset=0, size=0x2FFFFF)
OUT_OF_GAS_CALL_GAS = 400_000
FAILURE_SLOT = 11


def call_chains(depth: int) -> list:
    """Return every chain of `depth` call opcodes as a pytest parameter."""
    return [
        pytest.param(
            tuple(CALL_OPCODES[name] for name in names), id="_".join(names)
        )
        for names in product(CALL_OPCODES, repeat=depth)
    ]


@dataclass(frozen=True)
class Frame:
    """Execution context of one level of a call chain."""

    address: Address
    caller: Address
    value: int

    def enter(self, opcode: Op, callee: Address, value: int) -> "Frame":
        """Return the context in which `opcode` runs `callee`'s code."""
        if opcode in (Op.CALL, Op.STATICCALL):
            return Frame(address=callee, caller=self.address, value=value)
        if opcode == Op.CALLCODE:
            return Frame(
                address=self.address, caller=self.address, value=value
            )
        return self


def run_call_chain(
    state_test: StateTestFiller, pre: Alloc, chain: tuple[Op, ...]
) -> None:
    """
    Call down `chain`, one contract per opcode, and check each level's
    writes and balance and the context the innermost code observes.

    Level `n` stores its call's success in slot `n` and, below the top
    level, its CALLER in slot `CALLER_SLOT + n`.
    """
    depth = len(chain)
    sender = pre.fund_eoa()
    context_base = depth * 100

    # Construct the innermost contract.
    leaf_code = (
        Op.SSTORE(depth, 1)
        + Op.SSTORE(CALLER_SLOT, Op.CALLER)
        + Op.SSTORE(CALLVALUE_SLOT, Op.CALLVALUE)
        + Op.SSTORE(context_base + 30, Op.ADDRESS)
        + Op.SSTORE(context_base + 32, Op.ORIGIN)
        + Op.SSTORE(context_base + 36, Op.CALLDATASIZE)
        + Op.SSTORE(context_base + 38, Op.CODESIZE)
        + Op.SSTORE(context_base + 40, Op.GASPRICE)
        + Op.STOP
    )
    contracts = [pre.deploy_contract(code=leaf_code, balance=CONTRACT_BALANCE)]

    # Assign call values: the k-th call that carries a value sends k wei.
    values = []
    sent = 0
    for opcode in chain:
        if opcode != Op.DELEGATECALL:
            sent += 1
        values.append(0 if opcode == Op.DELEGATECALL else sent)

    # Construct the calling contracts, from the innermost one outward.
    for level in reversed(range(depth)):
        opcode = chain[level]
        if opcode == Op.DELEGATECALL:
            call = Op.SSTORE(
                level,
                opcode(
                    address=contracts[0], args_size=WINDOW, ret_size=WINDOW
                ),
            )
        else:
            call = Op.SSTORE(
                level,
                opcode(
                    address=contracts[0],
                    value=values[level],
                    args_size=WINDOW,
                    ret_size=WINDOW,
                ),
            )
        suffix = (
            Op.SSTORE(CALLER_SLOT + level, Op.CALLER)
            if level > 0
            else Bytecode()
        )
        contracts.insert(
            0,
            pre.deploy_contract(
                code=call + suffix + Op.STOP, balance=CONTRACT_BALANCE
            ),
        )

    # Construct the transaction.
    tx = Transaction(sender=sender, to=contracts[0], gas_price=GAS_PRICE)

    # Simulate each call's context and value transfer.
    frames = [Frame(address=contracts[0], caller=sender, value=0)]
    balance = dict.fromkeys(contracts, CONTRACT_BALANCE)
    for opcode, callee, value in zip(
        chain, contracts[1:], values, strict=True
    ):
        frame = frames[-1]
        if opcode == Op.CALL:
            balance[frame.address] -= value
            balance[callee] += value
        frames.append(frame.enter(opcode, callee, value))

    # Construct the expected storage.
    storage: dict[Address, dict[int, int | Address]] = {
        c: {} for c in contracts
    }
    for level, frame in enumerate(frames[:-1]):
        storage[frame.address][level] = 1
        if level > 0:
            storage[frame.address][CALLER_SLOT + level] = frame.caller
    leaf = frames[-1]
    storage[leaf.address].update(
        {
            depth: 1,
            CALLER_SLOT: leaf.caller,
            CALLVALUE_SLOT: leaf.value,
            context_base + 30: leaf.address,
            context_base + 32: sender,
            context_base + 36: WINDOW,
            context_base + 38: len(leaf_code),
            context_base + 40: GAS_PRICE,
        }
    )

    # Construct the expected post-state.
    post = {
        contract: Account(storage=storage[contract], balance=balance[contract])
        for contract in contracts
    }

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "state_tests/stCallCodes/callcallcall_000Filler.json",
        "state_tests/stCallCodes/callcallcallcode_001Filler.json",
        "state_tests/stCallCodes/callcallcodecall_010Filler.json",
        "state_tests/stCallCodes/callcallcodecallcode_011Filler.json",
        "state_tests/stCallCodes/callcodecallcall_100Filler.json",
        "state_tests/stCallCodes/callcodecallcallcode_101Filler.json",
        "state_tests/stCallCodes/callcodecallcodecall_110Filler.json",
        "state_tests/stCallCodes/callcodecallcodecallcode_111Filler.json",
        "state_tests/stCallDelegateCodesHomestead/callcallcallcode_001Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcallcodecall_010Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcallcodecallcode_011Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcall_100Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcallcode_101Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcodecall_110Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcodecallcode_111Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcallcode_001Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecall_010Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecallcode_011Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcall_100Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcallcode_101Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecall_110Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecallcode_111Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("chain", call_chains(3))
def test_three_level_call_chain(
    state_test: StateTestFiller, pre: Alloc, chain: tuple[Op, Op, Op]
) -> None:
    """Call -> call -> call -> code, every combination of call opcodes."""
    run_call_chain(state_test, pre, chain)


@pytest.mark.ported_from(
    [
        "state_tests/stCallCodes/callcall_00Filler.json",
        "state_tests/stCallCodes/callcallcode_01Filler.json",
        "state_tests/stCallCodes/callcodecall_10Filler.json",
        "state_tests/stCallCodes/callcodecallcode_11Filler.json",
        "state_tests/stCallDelegateCodesHomestead/callcallcode_01Filler.json",
        "state_tests/stCallDelegateCodesHomestead/callcodecall_10Filler.json",
        "state_tests/stCallDelegateCodesHomestead/callcodecallcode_11Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcode_01Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecall_10Filler.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcode_11Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("chain", call_chains(2))
def test_two_level_call_chain(
    state_test: StateTestFiller, pre: Alloc, chain: tuple[Op, Op]
) -> None:
    """Call -> call -> code, every combination of call opcodes."""
    run_call_chain(state_test, pre, chain)


@pytest.mark.ported_from(
    [
        "state_tests/stCallCodes/callcallcall_ABCB_RECURSIVEFiller.json",
        "state_tests/stCallCodes/callcallcallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcallcodecall_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcallcodecallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcodecallcall_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcodecallcallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcodecallcodecall_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcodecallcodecallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcallcallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcallcodecall_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcallcodecallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcall_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcodecall_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcodecallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecall_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcall_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecall_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("rounds", [0, 1, 40], ids=lambda r: f"rounds_{r}")
@pytest.mark.parametrize("chain", call_chains(3))
def test_recursive_call_chain(
    state_test: StateTestFiller,
    pre: Alloc,
    chain: tuple[Op, Op, Op],
    rounds: int,
) -> None:
    """
    Call A -> B -> C, where C calls B again for `rounds` more rounds of
    B -> C, and the last C calls B with no gas so that call fails.

    `rounds=0` is the outcome the fillers checked: their recursion ran until
    the gas ran out, but the first recursive B already failed, so only A,
    B and the first C kept their writes. 40 rounds is about as far as the
    fillers' recursion did any work before its gas thinned out.
    """
    a_to_b, b_to_c, c_to_b = chain

    # Construct C, which calls back the address it receives as calldata
    # with one round less, or with no gas once no rounds are left.
    rounds_left = Op.CALLDATALOAD(ROUNDS_OFFSET)
    c = pre.deploy_contract(
        code=Op.CALLDATACOPY(dest_offset=0, offset=0, size=WINDOW)
        + Op.MSTORE(ROUNDS_OFFSET, Op.SUB(rounds_left, 1))
        + Op.SSTORE(
            2,
            c_to_b(
                gas=Op.MUL(Op.GAS, Op.ISZERO(Op.ISZERO(rounds_left))),
                address=Op.CALLDATALOAD(0),
                args_size=WINDOW,
            ),
        )
        + Op.STOP,
        balance=CONTRACT_BALANCE,
    )

    # Construct B, which forwards its calldata to C.
    b = pre.deploy_contract(
        code=Op.CALLDATACOPY(dest_offset=0, offset=0, size=WINDOW)
        + Op.SSTORE(1, b_to_c(address=c, args_size=WINDOW))
        + Op.STOP,
        balance=CONTRACT_BALANCE,
    )

    # Construct A, which passes B's address and the round count down as
    # calldata.
    a = pre.deploy_contract(
        code=Op.MSTORE(0, b)
        + Op.MSTORE(ROUNDS_OFFSET, rounds)
        + Op.SSTORE(0, a_to_b(address=b, args_size=WINDOW))
        + Op.STOP,
        balance=CONTRACT_BALANCE,
    )

    # Construct the transaction.
    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=a)

    # Simulate the contexts of every frame, from A down to the last C,
    # with the slot each one stores its call's result in.
    frame = Frame(address=a, caller=sender, value=0)
    writes = [(frame, 0)]
    frame = frame.enter(a_to_b, b, 0)
    writes.append((frame, 1))
    frame = frame.enter(b_to_c, c, 0)
    writes.append((frame, 2))
    for _ in range(rounds):
        frame = frame.enter(c_to_b, b, 0)
        writes.append((frame, 1))
        frame = frame.enter(b_to_c, c, 0)
        writes.append((frame, 2))

    # Construct the expected storage: the frames store after their call
    # returns, innermost first; every call succeeds but the last C's.
    storage: dict[Address, dict[int, int]] = {a: {}, b: {}, c: {}}
    for index, (frame, slot) in reversed(list(enumerate(writes))):
        storage[frame.address][slot] = int(index < len(writes) - 1)

    # Construct the expected post-state.
    post = {
        contract: Account(storage=storage[contract], balance=CONTRACT_BALANCE)
        for contract in (a, b, c)
    }

    state_test(pre=pre, post=post, tx=tx)


def run_self_destruct_chain(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    chain: tuple[Op, ...],
    beneficiary_level: int,
    before_call: bool,
    send_value: bool,
) -> None:
    """
    Call down `chain` and SELFDESTRUCT the frame that makes the last call
    to the contract at `beneficiary_level`, after that call returns or,
    with `before_call`, before it is made.

    Level `n` stores its call's success in slot `n` and the innermost code
    stores 1 in slot `len(chain)`. A SELFDESTRUCT before the last call halts
    its frame, so neither that call nor anything below it runs.
    """
    depth = len(chain)
    sender = pre.fund_eoa()

    # Construct the innermost contract.
    contracts = [
        pre.deploy_contract(
            code=Op.SSTORE(depth, 1) + Op.STOP, balance=CONTRACT_BALANCE
        )
    ]

    # Construct the calling contracts, from the innermost one outward. The
    # top level passes the beneficiary down as calldata, the middle levels
    # forward it, and the last caller self-destructs to it, before or after
    # its call.
    values: list[int] = []
    for level in reversed(range(depth)):
        last_caller = level == depth - 1
        if level == 0:
            # The top level runs as itself, so it can name itself as the
            # beneficiary with ADDRESS.
            beneficiary = (
                Op.ADDRESS if beneficiary_level == 0 else contracts[0]
            )
            prefix = Op.MSTORE(0, beneficiary)
        elif not last_caller:
            prefix = Op.MSTORE(0, Op.CALLDATALOAD(0))
        elif before_call:
            prefix = Op.SELFDESTRUCT(Op.CALLDATALOAD(0))
        else:
            prefix = Bytecode()
        call_opcode = chain[level]
        if call_opcode in [Op.CALL, Op.CALLCODE]:
            call_value = level + 1 if send_value else 0
            call = Op.SSTORE(
                level,
                call_opcode(
                    address=contracts[0],
                    args_size=WINDOW,
                    ret_size=WINDOW,
                    value=call_value,
                ),
            )
            values.insert(0, call_value)
        else:
            call = Op.SSTORE(
                level,
                call_opcode(
                    address=contracts[0],
                    args_size=WINDOW,
                    ret_size=WINDOW,
                ),
            )
            values.insert(0, 0)

        suffix = (
            Op.SELFDESTRUCT(Op.CALLDATALOAD(0))
            if last_caller and not before_call
            else Bytecode()
        )
        contracts.insert(
            0,
            pre.deploy_contract(
                code=prefix + call + suffix + Op.STOP,
                balance=CONTRACT_BALANCE,
            ),
        )

    # Construct the transaction.
    tx = Transaction(sender=sender, to=contracts[0])

    # Simulate each call's context and the value moved by the calls that
    # run: with `before_call`, the last caller's call never does.
    frames = [Frame(address=contracts[0], caller=sender, value=0)]
    balance = dict.fromkeys(contracts, CONTRACT_BALANCE)
    calls_made = depth - 1 if before_call else depth
    for level, (opcode, callee, value) in enumerate(
        zip(chain, contracts[1:], values, strict=True)
    ):
        frame = frames[-1]
        if opcode == Op.CALL and level < calls_made:
            balance[frame.address] -= value
            balance[callee] += value
        frames.append(frame.enter(opcode, callee, value))
    destroyed = frames[depth - 1].address
    beneficiary_address = contracts[beneficiary_level]

    # Construct the expected storage: with `before_call`, the last caller
    # and the innermost code store nothing.
    storage: dict[Address, dict[int, int]] = {c: {} for c in contracts}
    storing = depth - 1 if before_call else depth + 1
    for level, frame in enumerate(frames[:storing]):
        storage[frame.address][level] = 1

    # Construct the expected balances: the destroyed account's balance
    # moves to the beneficiary, and before Cancun a self-destruct to itself
    # burns it.
    if beneficiary_address != destroyed:
        balance[beneficiary_address] += balance[destroyed]
        balance[destroyed] = 0
    elif fork < Cancun:
        balance[destroyed] = 0

    # Construct the expected post-state: before Cancun the destroyed
    # account is deleted.
    post: dict[Address, Account | None] = {
        contract: Account(storage=storage[contract], balance=balance[contract])
        for contract in contracts
    }
    if fork < Cancun:
        post[destroyed] = Account.NONEXISTENT

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "state_tests/stCallCodes/callcallcall_000_SuicideEndFiller.json",
        "state_tests/stCallCodes/callcallcallcode_001_SuicideEndFiller.json",
        "state_tests/stCallCodes/callcallcodecall_010_SuicideEndFiller.json",
        "state_tests/stCallCodes/callcallcodecallcode_011_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcodecallcall_100_SuicideEndFiller.json",
        "state_tests/stCallCodes/callcodecallcallcode_101_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcodecallcodecall_110_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcodecallcodecallcode_111_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcallcallcode_001_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcallcodecall_010_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcallcodecallcode_011_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcall_100_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcallcode_101_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcodecall_110_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcodecallcode_111_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcallcode_001_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecall_010_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecallcode_011_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcall_100_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcallcode_101_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecall_110_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecallcode_111_SuicideEndFiller.json",  # noqa: E501,
    ],
)
@pytest.mark.valid_from("SpuriousDragon")
@pytest.mark.parametrize("chain", call_chains(3))
def test_three_level_call_chain_suicide_end(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    chain: tuple[Op, Op, Op],
) -> None:
    """Call -> call -> (call -> code) self-destruct to the first callee."""
    run_self_destruct_chain(
        state_test,
        pre,
        fork,
        chain,
        beneficiary_level=1,
        before_call=False,
        send_value=False,
    )


@pytest.mark.ported_from(
    [
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecallcode_111_SuicideEndFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("SpuriousDragon")
@pytest.mark.parametrize("chain", call_chains(3))
def test_three_level_call_chain_suicide_end_with_value(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    chain: tuple[Op, Op, Op],
) -> None:
    """Call -> call -> (call -> code) self-destruct to the first callee."""
    run_self_destruct_chain(
        state_test,
        pre,
        fork,
        chain,
        beneficiary_level=1,
        before_call=False,
        send_value=True,
    )


@pytest.mark.ported_from(
    [
        "state_tests/stCallCodes/callcall_00_SuicideEndFiller.json",
        "state_tests/stCallCodes/callcallcode_01_SuicideEndFiller.json",
        "state_tests/stCallCodes/callcodecall_10_SuicideEndFiller.json",
        "state_tests/stCallCodes/callcodecallcode_11_SuicideEndFiller.json",
        "state_tests/stCallDelegateCodesHomestead/callcallcode_01_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecall_10_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcode_11_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcode_01_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecall_10_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcode_11_SuicideEndFiller.json",  # noqa: E501,
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("chain", call_chains(2))
def test_two_level_call_chain_suicide_end(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    chain: tuple[Op, Op],
) -> None:
    """Call -> (call -> code) self-destruct to the top level."""
    run_self_destruct_chain(
        state_test,
        pre,
        fork,
        chain,
        beneficiary_level=0,
        before_call=False,
        send_value=False,
    )


@pytest.mark.ported_from(
    [
        "state_tests/stCallCodes/callcallcall_000_SuicideMiddleFiller.json",
        "state_tests/stCallCodes/callcallcallcode_001_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcallcodecall_010_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcallcodecallcode_011_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcodecallcall_100_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcodecallcallcode_101_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcodecallcodecall_110_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcodecallcodecallcode_111_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcallcallcode_001_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcallcodecall_010_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcallcodecallcode_011_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcall_100_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcallcode_101_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcodecall_110_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcodecallcode_111_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcallcode_001_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecall_010_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecallcode_011_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcall_100_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcallcode_101_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecall_110_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecallcode_111_SuicideMiddleFiller.json",  # noqa: E501,
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("chain", call_chains(3))
def test_three_level_call_chain_suicide_middle(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    chain: tuple[Op, Op, Op],
) -> None:
    """Call -> call -> (self-destruct to the top level) call -> code."""
    run_self_destruct_chain(
        state_test,
        pre,
        fork,
        chain,
        beneficiary_level=0,
        before_call=True,
        send_value=False,
    )


def run_out_of_gas_chain(
    state_test: StateTestFiller,
    pre: Alloc,
    chain: tuple[Op, ...],
    values: tuple[int, ...],
    failing_level: int,
    after_call: bool,
) -> None:
    """
    Call down `chain`, with the frame at `failing_level` running out of gas
    before or, with `after_call`, after its own call. A failing innermost
    frame runs out of gas after its store instead.

    Level `n` stores its call's success in slot `n`, and the caller of the
    failing frame stores 1 in `FAILURE_SLOT` after the failed call. The
    failing frame's writes and everything below it are reverted.
    """
    depth = len(chain)
    sender = pre.fund_eoa()

    # Construct the innermost contract.
    leaf_suffix = OUT_OF_GAS_MEMORY if failing_level == depth else Bytecode()
    contracts = [
        pre.deploy_contract(
            code=Op.SSTORE(depth, 1) + leaf_suffix + Op.STOP,
            balance=CONTRACT_BALANCE,
        )
    ]

    # Construct the calling contracts, from the innermost one outward. Only
    # the call into the failing frame has bounded gas.
    for level in reversed(range(depth)):
        opcode = chain[level]
        gas = OUT_OF_GAS_CALL_GAS if level == failing_level - 1 else Op.GAS
        failing = level == failing_level
        prefix = (
            OUT_OF_GAS_MEMORY if failing and not after_call else Bytecode()
        )
        if opcode == Op.DELEGATECALL:
            call = Op.SSTORE(
                level,
                opcode(
                    gas=gas,
                    address=contracts[0],
                    args_size=WINDOW,
                    ret_size=WINDOW,
                ),
            )
        else:
            call = Op.SSTORE(
                level,
                opcode(
                    gas=gas,
                    address=contracts[0],
                    value=values[level],
                    args_size=WINDOW,
                    ret_size=WINDOW,
                ),
            )
        if failing and after_call:
            suffix = OUT_OF_GAS_MEMORY
        elif level == failing_level - 1:
            suffix = Op.SSTORE(FAILURE_SLOT, 1)
        else:
            suffix = Bytecode()
        contracts.insert(
            0,
            pre.deploy_contract(
                code=prefix + call + suffix + Op.STOP,
                balance=CONTRACT_BALANCE,
            ),
        )

    # Construct the transaction.
    tx = Transaction(sender=sender, to=contracts[0])

    # Simulate each call's context and the value moved by the calls that
    # succeed, which are those above the failing frame's caller.
    frames = [Frame(address=contracts[0], caller=sender, value=0)]
    balance = dict.fromkeys(contracts, CONTRACT_BALANCE)
    for level, (opcode, callee, value) in enumerate(
        zip(chain, contracts[1:], values, strict=True)
    ):
        frame = frames[-1]
        if opcode == Op.CALL and level < failing_level - 1:
            balance[frame.address] -= value
            balance[callee] += value
        frames.append(frame.enter(opcode, callee, value))

    # Construct the expected storage: the failed call stores 0.
    storage: dict[Address, dict[int, int]] = {c: {} for c in contracts}
    for level in range(failing_level - 1):
        storage[frames[level].address][level] = 1
    storage[frames[failing_level - 1].address][FAILURE_SLOT] = 1

    # Construct the expected post-state.
    post = {
        contract: Account(storage=storage[contract], balance=balance[contract])
        for contract in contracts
    }

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "state_tests/stCallCodes/callcallcall_000_OOGEFiller.json",
        "state_tests/stCallCodes/callcallcallcode_001_OOGEFiller.json",
        "state_tests/stCallCodes/callcallcodecall_010_OOGEFiller.json",
        "state_tests/stCallCodes/callcallcodecallcode_011_OOGEFiller.json",
        "state_tests/stCallCodes/callcodecallcall_100_OOGEFiller.json",
        "state_tests/stCallCodes/callcodecallcallcode_101_OOGEFiller.json",
        "state_tests/stCallCodes/callcodecallcodecall_110_OOGEFiller.json",
        "state_tests/stCallCodes/callcodecallcodecallcode_111_OOGEFiller.json",
        "state_tests/stCallDelegateCodesHomestead/callcallcallcode_001_OOGEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcallcodecall_010_OOGEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcallcodecallcode_011_OOGEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcall_100_OOGEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcallcode_101_OOGEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcodecall_110_OOGEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcodecallcode_111_OOGEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcallcode_001_OOGEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecall_010_OOGEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecallcode_011_OOGEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcall_100_OOGEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcallcode_101_OOGEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecall_110_OOGEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecallcode_111_OOGEFiller.json",  # noqa: E501,
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("chain", call_chains(3))
def test_three_level_call_chain_ooge(
    state_test: StateTestFiller, pre: Alloc, chain: tuple[Op, Op, Op]
) -> None:
    """Call -> call -> call -> code that runs out of gas."""
    run_out_of_gas_chain(
        state_test,
        pre,
        chain,
        values=(0, 0, 0),
        failing_level=3,
        after_call=True,
    )


@pytest.mark.ported_from(
    [
        "state_tests/stCallCodes/callcall_00_OOGEFiller.json",
        "state_tests/stCallCodes/callcallcode_01_OOGEFiller.json",
        "state_tests/stCallCodes/callcodecall_10_OOGEFiller.json",
        "state_tests/stCallCodes/callcodecallcode_11_OOGEFiller.json",
        "state_tests/stCallDelegateCodesHomestead/callcallcode_01_OOGEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecall_10_OOGEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcode_11_OOGEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcode_01_OOGEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecall_10_OOGEFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcode_11_OOGEFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcall_00_OOGE_valueTransferFiller.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "values",
    [
        pytest.param((0, 0), id="no_value"),
        pytest.param((20, 10), id="with_value"),
    ],
)
@pytest.mark.parametrize("chain", call_chains(2))
def test_two_level_call_chain_ooge(
    state_test: StateTestFiller,
    pre: Alloc,
    chain: tuple[Op, Op],
    values: tuple[int, int],
) -> None:
    """
    Call -> call -> code that runs out of gas, with and without value on
    the calls that carry one.
    """
    run_out_of_gas_chain(
        state_test,
        pre,
        chain,
        values=values,
        failing_level=2,
        after_call=True,
    )


@pytest.mark.ported_from(
    [
        "state_tests/stCallCodes/callcallcall_000_OOGMBeforeFiller.json",
        "state_tests/stCallCodes/callcallcallcode_001_OOGMBeforeFiller.json",
        "state_tests/stCallCodes/callcallcodecall_010_OOGMBeforeFiller.json",
        "state_tests/stCallCodes/callcallcodecallcode_011_OOGMBeforeFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcodecallcall_100_OOGMBeforeFiller.json",
        "state_tests/stCallCodes/callcodecallcallcode_101_OOGMBeforeFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcodecallcodecall_110_OOGMBeforeFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcodecallcodecallcode_111_OOGMBeforeFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcallcallcode_001_OOGMBeforeFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcallcodecall_010_OOGMBeforeFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcallcodecallcode_011_OOGMBeforeFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcall_100_OOGMBeforeFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcallcode_101_OOGMBeforeFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcodecall_110_OOGMBeforeFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcodecallcode_111_OOGMBeforeFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcallcode_001_OOGMBeforeFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecall_010_OOGMBeforeFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecallcode_011_OOGMBeforeFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcall_100_OOGMBeforeFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcallcode_101_OOGMBeforeFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecall_110_OOGMBeforeFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecallcode_111_OOGMBeforeFiller.json",  # noqa: E501,
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("chain", call_chains(3))
def test_three_level_call_chain_oogm_before(
    state_test: StateTestFiller, pre: Alloc, chain: tuple[Op, Op, Op]
) -> None:
    """Call -> call -> (out of gas) call -> code."""
    run_out_of_gas_chain(
        state_test,
        pre,
        chain,
        values=(0, 0, 0),
        failing_level=2,
        after_call=False,
    )


@pytest.mark.ported_from(
    [
        "state_tests/stCallCodes/callcallcall_000_OOGMAfterFiller.json",
        "state_tests/stCallCodes/callcallcallcode_001_OOGMAfterFiller.json",
        "state_tests/stCallCodes/callcallcodecall_010_OOGMAfterFiller.json",
        "state_tests/stCallCodes/callcallcodecallcode_011_OOGMAfterFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcodecallcall_100_OOGMAfterFiller.json",
        "state_tests/stCallCodes/callcodecallcallcode_101_OOGMAfterFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcodecallcodecall_110_OOGMAfterFiller.json",  # noqa: E501
        "state_tests/stCallCodes/callcodecallcodecallcode_111_OOGMAfterFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcallcallcode_001_OOGMAfterFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcallcodecall_010_OOGMAfterFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcallcodecallcode_011_OOGMAfterFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcall_100_OOGMAfterFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcallcode_101_OOGMAfterFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcodecall_110_OOGMAfterFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesHomestead/callcodecallcodecallcode_111_OOGMAfterFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcallcode_001_OOGMAfterFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecall_010_OOGMAfterFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecallcode_011_OOGMAfterFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcall_100_OOGMAfterFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcallcode_101_OOGMAfterFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecall_110_OOGMAfterFiller.json",  # noqa: E501
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcodecallcodecallcode_111_OOGMAfterFiller.json",  # noqa: E501,
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("chain", call_chains(3))
def test_three_level_call_chain_oogm_after(
    state_test: StateTestFiller, pre: Alloc, chain: tuple[Op, Op, Op]
) -> None:
    """Call -> (call -> call -> code) out of gas."""
    run_out_of_gas_chain(
        state_test,
        pre,
        chain,
        values=(0, 0, 0),
        failing_level=1,
        after_call=True,
    )


STATIC_CALL_OPCODES = {**CALL_OPCODES, "staticcall": Op.STATICCALL}
RETURN_SIZE = 0x80
SUCCESS_OFFSET = 0x80
RESULT_SLOTS = {"count": 0x10, "caller": 0x11, "value": 0x12, "address": 0x13}
FAULT_SLOT = 0x1F
DONE_SLOT = 0x1E


def static_call_chains(depth: int) -> list:
    """
    Return every chain of `depth` call opcodes, STATICCALL included, that
    has at least one STATICCALL, as a pytest parameter.
    """
    return [
        pytest.param(
            tuple(STATIC_CALL_OPCODES[name] for name in names),
            id="_".join(names),
        )
        for names in product(STATIC_CALL_OPCODES, repeat=depth)
        if "staticcall" in names
    ]


@dataclass
class StaticChainResult:
    """Outcome of one frame of a simulated static call chain."""

    success: bool
    returned: tuple[int | Address, ...] | None
    effects: list[tuple]


def run_static_call_chain(
    state_test: StateTestFiller,
    pre: Alloc,
    chain: tuple[Op, ...],
    *,
    value: int = 0,
    fault: str | None = None,
    fault_level: int = 0,
    before_call: bool = False,
) -> None:
    """
    Call down `chain`, one contract per opcode, and check what the top level
    learns from the frames below and where non-static frames' writes land.

    Every frame below the top returns `RETURN_SIZE` bytes: the number of
    frames below it that returned, plus one for its own call's success,
    followed by the innermost frame's CALLER, CALLVALUE and ADDRESS. The
    top level stores them in `RESULT_SLOTS` and then sets `DONE_SLOT`; a
    non-static level `n` also stores its call's success in slot `n`. CALL
    and CALLCODE carry `value`.

    `fault` is injected in the frame at `fault_level` (the innermost frame
    when it equals the chain's length), before or after its call:
    `"sstore"` writes `FAULT_SLOT`, `"out_of_gas"` expands memory until it
    runs out of gas (only the call into it has bounded gas), and
    `"self_destruct"` self-destructs to a fresh beneficiary.
    """
    depth = len(chain)
    static = [
        any(opcode == Op.STATICCALL for opcode in chain[:level])
        for level in range(depth + 1)
    ]
    beneficiary = pre.nonexistent_account()

    def fault_code(level: int) -> Bytecode:
        if fault is None or level != fault_level:
            return Bytecode()
        if fault == "sstore":
            return Op.SSTORE(FAULT_SLOT, 1)
        if fault == "out_of_gas":
            return OUT_OF_GAS_MEMORY
        if fault == "self_destruct":
            return Op.SELFDESTRUCT(beneficiary)
        raise ValueError(f"Unknown fault: {fault}")

    def call_value(opcode: Op) -> int:
        return value if opcode in (Op.CALL, Op.CALLCODE) else 0

    # Construct the innermost contract.
    contracts = [
        pre.deploy_contract(
            code=fault_code(depth)
            + Op.MSTORE(0x00, 1)
            + Op.MSTORE(0x20, Op.CALLER)
            + Op.MSTORE(0x40, Op.CALLVALUE)
            + Op.MSTORE(0x60, Op.ADDRESS)
            + Op.RETURN(0, RETURN_SIZE),
            balance=CONTRACT_BALANCE,
        )
    ]

    # Construct the calling contracts, from the innermost one outward.
    for level in reversed(range(depth)):
        opcode = chain[level]
        gas = (
            OUT_OF_GAS_CALL_GAS
            if fault == "out_of_gas" and level == fault_level - 1
            else Op.GAS
        )
        if opcode in (Op.CALL, Op.CALLCODE):
            call = opcode(
                gas=gas,
                address=contracts[0],
                value=call_value(opcode),
                ret_size=RETURN_SIZE,
            )
        else:
            call = opcode(gas=gas, address=contracts[0], ret_size=RETURN_SIZE)
        code = (
            (fault_code(level) if before_call else Bytecode())
            + Op.MSTORE(SUCCESS_OFFSET, call)
            + Op.MSTORE(0, Op.ADD(Op.MLOAD(0), Op.MLOAD(SUCCESS_OFFSET)))
        )
        if not static[level]:
            code += Op.SSTORE(level, Op.MLOAD(SUCCESS_OFFSET))
        if not before_call:
            code += fault_code(level)
        if level == 0:
            code += (
                Op.SSTORE(RESULT_SLOTS["count"], Op.MLOAD(0x00))
                + Op.SSTORE(RESULT_SLOTS["caller"], Op.MLOAD(0x20))
                + Op.SSTORE(RESULT_SLOTS["value"], Op.MLOAD(0x40))
                + Op.SSTORE(RESULT_SLOTS["address"], Op.MLOAD(0x60))
                + Op.SSTORE(DONE_SLOT, 1)
                + Op.STOP
            )
        else:
            code += Op.RETURN(0, RETURN_SIZE)
        contracts.insert(
            0, pre.deploy_contract(code=code, balance=CONTRACT_BALANCE)
        )

    # Construct the transaction.
    sender = pre.fund_eoa()
    tx = Transaction(sender=sender, to=contracts[0])

    # Simulate each frame's context.
    frames = [Frame(address=contracts[0], caller=sender, value=0)]
    for opcode, callee in zip(chain, contracts[1:], strict=True):
        frames.append(frames[-1].enter(opcode, callee, call_value(opcode)))

    def apply_fault(level: int) -> StaticChainResult | None:
        """Return the frame's outcome if the fault ends it."""
        if fault is None or level != fault_level:
            return None
        if fault == "out_of_gas" or static[level]:
            return StaticChainResult(False, None, [])
        if fault == "self_destruct":
            return StaticChainResult(
                True, None, [("destroy", frames[level].address)]
            )
        return None

    def run(level: int) -> StaticChainResult:
        """Simulate the frame at `level` and everything below it."""
        effects: list[tuple] = []
        if level == depth or before_call:
            ended = apply_fault(level)
            if ended is not None:
                return ended
            if fault == "sstore" and level == fault_level:
                effects.append(("store", frames[level].address, FAULT_SLOT, 1))
        if level == depth:
            leaf = frames[depth]
            return StaticChainResult(
                True, (1, leaf.caller, leaf.value, leaf.address), effects
            )
        opcode = chain[level]
        sent = call_value(opcode)
        if static[level] and opcode == Op.CALL and sent > 0:
            return StaticChainResult(False, None, [])
        callee = run(level + 1)
        returned: tuple[int | Address, ...] = (0, 0, 0, 0)
        if callee.success:
            if opcode == Op.CALL and sent > 0:
                effects.append(
                    (
                        "transfer",
                        frames[level].address,
                        contracts[level + 1],
                        sent,
                    )
                )
            effects += callee.effects
            if callee.returned is not None:
                returned = callee.returned
        count = int(returned[0]) + int(callee.success)
        returned = (count, *returned[1:])
        if not static[level]:
            effects.append(
                ("store", frames[level].address, level, int(callee.success))
            )
        if not before_call:
            ended = apply_fault(level)
            if ended is not None:
                return StaticChainResult(
                    ended.success,
                    None,
                    effects + ended.effects if ended.success else [],
                )
            if fault == "sstore" and level == fault_level:
                effects.append(("store", frames[level].address, FAULT_SLOT, 1))
        if level == 0:
            for key, word in zip(RESULT_SLOTS.values(), returned, strict=True):
                effects.append(("store", contracts[0], key, word))
            effects.append(("store", contracts[0], DONE_SLOT, 1))
        return StaticChainResult(True, returned, effects)

    # Apply the simulated effects to the pre-state.
    storage: dict[Address, dict[int, int | Address]] = {
        c: {} for c in contracts
    }
    balance = dict.fromkeys(contracts, CONTRACT_BALANCE)
    balance[beneficiary] = 0
    for effect in run(0).effects:
        if effect[0] == "store":
            _, address, slot, word = effect
            storage[address][slot] = word
        elif effect[0] == "transfer":
            _, source, destination, amount = effect
            balance[source] -= amount
            balance[destination] += amount
        else:
            _, destroyed = effect
            balance[beneficiary] += balance[destroyed]
            balance[destroyed] = 0

    # Construct the expected post-state.
    post: dict[Address, Account | None] = {
        contract: Account(storage=storage[contract], balance=balance[contract])
        for contract in contracts
    }
    post[beneficiary] = (
        Account(balance=balance[beneficiary])
        if balance[beneficiary] > 0
        else Account.NONEXISTENT
    )

    state_test(pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_callcall_00Filler.json",
        "state_tests/stStaticCall/static_callcallcall_000Filler.json",
        "state_tests/stStaticCall/static_callcallcallcode_001Filler.json",
        "state_tests/stStaticCall/static_callcallcallcode_001_2Filler.json",
        "state_tests/stStaticCall/static_callcallcode_01_2Filler.json",
        "state_tests/stStaticCall/static_callcallcodecall_010Filler.json",
        "state_tests/stStaticCall/static_callcallcodecall_010_2Filler.json",
        "state_tests/stStaticCall/static_callcallcodecallcode_011Filler.json",
        "state_tests/stStaticCall/static_callcallcodecallcode_011_2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecall_10Filler.json",
        "state_tests/stStaticCall/static_callcodecall_10_2Filler.json",
        "state_tests/stStaticCall/static_callcodecallcall_100Filler.json",
        "state_tests/stStaticCall/static_callcodecallcall_100_2Filler.json",
        "state_tests/stStaticCall/static_callcodecallcallcode_101Filler.json",
        "state_tests/stStaticCall/static_callcodecallcallcode_101_2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcodecall_1102Filler.json",
        "state_tests/stStaticCall/static_callcodecallcodecall_110Filler.json",
        "state_tests/stStaticCall/static_callcodecallcodecall_110_2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_calldelcode_01Filler.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("value", [0, 1], ids=["no_value", "with_value"])
@pytest.mark.parametrize(
    "leaf_writes", [False, True], ids=["leaf_reads", "leaf_writes"]
)
@pytest.mark.parametrize(
    "chain", static_call_chains(2) + static_call_chains(3)
)
def test_static_call_chain(
    state_test: StateTestFiller,
    pre: Alloc,
    chain: tuple[Op, ...],
    leaf_writes: bool,
    value: int,
) -> None:
    """
    Call down a chain with a STATICCALL in it to code that only reads its
    context or, with `leaf_writes`, first writes storage.
    """
    run_static_call_chain(
        state_test,
        pre,
        chain,
        value=value,
        fault="sstore" if leaf_writes else None,
        fault_level=len(chain),
    )


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_callcall_00_OOGEFiller.json",
        "state_tests/stStaticCall/static_callcall_00_OOGE_1Filler.json",
        "state_tests/stStaticCall/static_callcall_00_OOGE_2Filler.json",
        "state_tests/stStaticCall/static_callcallcall_000_OOGEFiller.json",
        "state_tests/stStaticCall/static_callcallcall_000_OOGMAfter2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcall_000_OOGMAfterFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcall_000_OOGMBeforeFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcallcode_001_OOGEFiller.json",
        "state_tests/stStaticCall/static_callcallcallcode_001_OOGE_2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcallcode_001_OOGMAfter2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcallcode_001_OOGMAfterFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcallcode_001_OOGMAfter_2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcallcode_001_OOGMAfter_3Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcallcode_001_OOGMBefore2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcallcode_001_OOGMBeforeFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcode_01_OOGE_2Filler.json",
        "state_tests/stStaticCall/static_callcallcodecall_010_OOGEFiller.json",
        "state_tests/stStaticCall/static_callcallcodecall_010_OOGE_2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcodecall_010_OOGMAfter2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcodecall_010_OOGMAfterFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcodecall_010_OOGMAfter_2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcodecall_010_OOGMAfter_3Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcodecall_010_OOGMBefore2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcodecall_010_OOGMBeforeFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcodecallcode_011_OOGEFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcodecallcode_011_OOGE_2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcodecallcode_011_OOGMAfter2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcodecallcode_011_OOGMAfterFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcodecallcode_011_OOGMAfter_1Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcodecallcode_011_OOGMAfter_2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcodecallcode_011_OOGMBefore2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcodecallcode_011_OOGMBeforeFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecall_10_OOGEFiller.json",
        "state_tests/stStaticCall/static_callcodecall_10_OOGE_2Filler.json",
        "state_tests/stStaticCall/static_callcodecallcall_100_OOGE2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcall_100_OOGEFiller.json",
        "state_tests/stStaticCall/static_callcodecallcall_100_OOGMAfter2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcall_100_OOGMAfterFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcall_100_OOGMAfter_2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcall_100_OOGMAfter_3Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcall_100_OOGMBefore2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcall_100_OOGMBeforeFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcallcode_101_OOGEFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcallcode_101_OOGE_2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcallcode_101_OOGMAfter2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcallcode_101_OOGMAfterFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcallcode_101_OOGMAfter_1Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcallcode_101_OOGMAfter_3Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcallcode_101_OOGMBefore2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcallcode_101_OOGMBeforeFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcodecall_110_OOGE2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcodecall_110_OOGEFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcodecall_110_OOGMAfter2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcodecall_110_OOGMAfterFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcodecall_110_OOGMAfter_2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcodecall_110_OOGMAfter_3Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcodecall_110_OOGMBefore2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcodecall_110_OOGMBeforeFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_calldelcode_01_OOGEFiller.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "from_end, before_call",
    [
        pytest.param(0, False, id="ooge"),
        pytest.param(1, True, id="oogm_before"),
        pytest.param(1, False, id="oogm_after"),
    ],
)
@pytest.mark.parametrize(
    "chain", static_call_chains(2) + static_call_chains(3)
)
def test_static_call_chain_out_of_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    chain: tuple[Op, ...],
    from_end: int,
    before_call: bool,
) -> None:
    """
    Call down a chain with a STATICCALL in it, where the innermost frame,
    or the frame calling it (before or after its call), runs out of gas.
    """
    run_static_call_chain(
        state_test,
        pre,
        chain,
        fault="out_of_gas",
        fault_level=len(chain) - from_end,
        before_call=before_call,
    )


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_callcall_00_SuicideEndFiller.json",
        "state_tests/stStaticCall/static_callcallcall_000_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcall_000_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcallcode_001_SuicideEnd2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcallcode_001_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcallcode_001_SuicideMiddle2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcallcode_001_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcode_01_SuicideEnd2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcode_01_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcodecall_010_SuicideEnd2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcodecall_010_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcodecall_010_SuicideMiddle2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcodecall_010_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcodecallcode_011_SuicideEnd2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcodecallcode_011_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcodecallcode_011_SuicideMiddle2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcodecallcode_011_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecall_10_SuicideEnd2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecall_10_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcall_100_SuicideEnd2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcall_100_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcall_100_SuicideMiddle2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcall_100_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcallcode_101_SuicideEnd2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcallcode_101_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcallcode_101_SuicideMiddle2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcallcode_101_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcodecall_110_SuicideEnd2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcodecall_110_SuicideEndFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcodecall_110_SuicideMiddle2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcodecall_110_SuicideMiddleFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcodecallcode_111_SuicideEndFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "before_call",
    [
        pytest.param(False, id="suicide_end"),
        pytest.param(True, id="suicide_middle"),
    ],
)
@pytest.mark.parametrize(
    "chain", static_call_chains(2) + static_call_chains(3)
)
def test_static_call_chain_self_destruct(
    state_test: StateTestFiller,
    pre: Alloc,
    chain: tuple[Op, ...],
    before_call: bool,
) -> None:
    """
    Call down a chain with a STATICCALL in it, where the frame calling the
    innermost code self-destructs before or after its call.
    """
    run_static_call_chain(
        state_test,
        pre,
        chain,
        fault="self_destruct",
        fault_level=len(chain) - 1,
        before_call=before_call,
    )


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_callcallcall_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcallcode_ABCB_RECURSIVE2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcodecall_ABCB_RECURSIVE2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcodecall_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcodecallcode_ABCB_RECURSIVE2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcallcodecallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcall_ABCB_RECURSIVE2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcall_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcallcode_ABCB_RECURSIVE2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcallcode_ABCB_RECURSIVEFiller.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcodecall_ABCB_RECURSIVE2Filler.json",  # noqa: E501
        "state_tests/stStaticCall/static_callcodecallcodecall_ABCB_RECURSIVEFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize("rounds", [0, 1, 40], ids=lambda r: f"rounds_{r}")
@pytest.mark.parametrize("chain", static_call_chains(3))
def test_static_recursive_call_chain(
    state_test: StateTestFiller,
    pre: Alloc,
    chain: tuple[Op, Op, Op],
    rounds: int,
) -> None:
    """
    Call A -> B -> C, where C calls B again for `rounds` more rounds of
    B -> C, and the last C calls B with no gas so that call fails.

    Every frame returns how many frames below it returned, plus one for its
    own call's success, and A stores it, so the recursion is observable
    through the static frames, which cannot write.
    """
    a_to_b, b_to_c, c_to_b = chain
    count_offset = 2 * ROUNDS_OFFSET
    count_and_return = Op.MSTORE(
        count_offset, Op.ADD(Op.MLOAD(count_offset), Op.MLOAD(SUCCESS_OFFSET))
    ) + Op.RETURN(count_offset, 32)

    # Construct C, which calls back the address it receives as calldata
    # with one round less, or with no gas once no rounds are left.
    rounds_left = Op.CALLDATALOAD(ROUNDS_OFFSET)
    c = pre.deploy_contract(
        code=Op.CALLDATACOPY(dest_offset=0, offset=0, size=WINDOW)
        + Op.MSTORE(ROUNDS_OFFSET, Op.SUB(rounds_left, 1))
        + Op.MSTORE(
            SUCCESS_OFFSET,
            c_to_b(
                gas=Op.MUL(Op.GAS, Op.ISZERO(Op.ISZERO(rounds_left))),
                address=Op.CALLDATALOAD(0),
                args_size=WINDOW,
                ret_offset=count_offset,
                ret_size=32,
            ),
        )
        + count_and_return,
        balance=CONTRACT_BALANCE,
    )

    # Construct B, which forwards its calldata to C.
    b = pre.deploy_contract(
        code=Op.CALLDATACOPY(dest_offset=0, offset=0, size=WINDOW)
        + Op.MSTORE(
            SUCCESS_OFFSET,
            b_to_c(
                address=c,
                args_size=WINDOW,
                ret_offset=count_offset,
                ret_size=32,
            ),
        )
        + count_and_return,
        balance=CONTRACT_BALANCE,
    )

    # Construct A, which passes B's address and the round count down as
    # calldata and stores the count.
    a = pre.deploy_contract(
        code=Op.MSTORE(0, b)
        + Op.MSTORE(ROUNDS_OFFSET, rounds)
        + Op.MSTORE(
            SUCCESS_OFFSET,
            a_to_b(
                address=b,
                args_size=WINDOW,
                ret_offset=count_offset,
                ret_size=32,
            ),
        )
        + Op.SSTORE(
            0, Op.ADD(Op.MLOAD(count_offset), Op.MLOAD(SUCCESS_OFFSET))
        )
        + Op.STOP,
        balance=CONTRACT_BALANCE,
    )

    # Construct the transaction.
    tx = Transaction(sender=pre.fund_eoa(), to=a)

    # Every call but the last C's succeeds: A, B and C, then two frames per
    # round, each count one call.
    post = {
        a: Account(storage={0: 2 + 2 * rounds}, balance=CONTRACT_BALANCE),
        b: Account(storage={}, balance=CONTRACT_BALANCE),
        c: Account(storage={}, balance=CONTRACT_BALANCE),
    }

    state_test(pre=pre, post=post, tx=tx)
