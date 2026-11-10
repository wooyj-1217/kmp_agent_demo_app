"""Generate only the new Teum project's project file; no prior project inputs."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
project = root / "ios/Teum.xcodeproj"
project.mkdir(exist_ok=True)
(project / "project.pbxproj").write_text('''// !$*UTF8*$!
{
 archiveVersion = 1; classes = {}; objectVersion = 56;
 objects = {
 A00000000000000000000001 = {isa = PBXProject; attributes = {LastUpgradeCheck = 1600;}; buildConfigurationList = A00000000000000000000002; compatibilityVersion = "Xcode 14.0"; developmentRegion = ko; knownRegions = (ko,en,Base); mainGroup = A00000000000000000000003; productRefGroup = A00000000000000000000004; projectDirPath = ""; projectRoot = ""; targets = (A00000000000000000000005);};
 A00000000000000000000002 = {isa = XCConfigurationList; buildConfigurations = (A00000000000000000000011,A00000000000000000000012); defaultConfigurationIsVisible = 0; defaultConfigurationName = Release;};
 A00000000000000000000003 = {isa = PBXGroup; children = (A00000000000000000000006,A00000000000000000000007,A00000000000000000000004); sourceTree = "<group>";};
 A00000000000000000000004 = {isa = PBXGroup; children = (A00000000000000000000008); name = Products; sourceTree = "<group>";};
 A00000000000000000000005 = {isa = PBXNativeTarget; buildConfigurationList = A00000000000000000000009; buildPhases = (A0000000000000000000000A,A0000000000000000000000B,A0000000000000000000000C); buildRules = (); dependencies = (); name = Teum; productName = Teum; productReference = A00000000000000000000008; productType = "com.apple.product-type.application";};
 A00000000000000000000006 = {isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = Teum/TeumApp.swift; sourceTree = "<group>";};
 A00000000000000000000007 = {isa = PBXFileReference; lastKnownFileType = folder; name = web; path = ../web; sourceTree = "<group>";};
 A00000000000000000000008 = {isa = PBXFileReference; explicitFileType = wrapper.application; includeInIndex = 0; path = Teum.app; sourceTree = BUILT_PRODUCTS_DIR;};
 A00000000000000000000009 = {isa = XCConfigurationList; buildConfigurations = (A00000000000000000000013,A00000000000000000000014); defaultConfigurationIsVisible = 0; defaultConfigurationName = Release;};
 A0000000000000000000000A = {isa = PBXSourcesBuildPhase; buildActionMask = 2147483647; files = (A0000000000000000000000D); runOnlyForDeploymentPostprocessing = 0;};
 A0000000000000000000000B = {isa = PBXFrameworksBuildPhase; buildActionMask = 2147483647; files = (); runOnlyForDeploymentPostprocessing = 0;};
 A0000000000000000000000C = {isa = PBXResourcesBuildPhase; buildActionMask = 2147483647; files = (A0000000000000000000000E); runOnlyForDeploymentPostprocessing = 0;};
 A0000000000000000000000D = {isa = PBXBuildFile; fileRef = A00000000000000000000006;};
 A0000000000000000000000E = {isa = PBXBuildFile; fileRef = A00000000000000000000007;};
 A00000000000000000000011 = {isa = XCBuildConfiguration; buildSettings = {SDKROOT = iphoneos; IPHONEOS_DEPLOYMENT_TARGET = 16.0; SWIFT_VERSION = 5.0; CLANG_ENABLE_MODULES = YES; DEBUG_INFORMATION_FORMAT = dwarf;}; name = Debug;};
 A00000000000000000000012 = {isa = XCBuildConfiguration; buildSettings = {SDKROOT = iphoneos; IPHONEOS_DEPLOYMENT_TARGET = 16.0; SWIFT_VERSION = 5.0; CLANG_ENABLE_MODULES = YES;}; name = Release;};
 A00000000000000000000013 = {isa = XCBuildConfiguration; buildSettings = {PRODUCT_BUNDLE_IDENTIFIER = app.teum.memo; PRODUCT_NAME = "$(TARGET_NAME)"; INFOPLIST_FILE = Teum/Info.plist; TARGETED_DEVICE_FAMILY = "1,2"; SWIFT_OPTIMIZATION_LEVEL = "-Onone"; CODE_SIGN_STYLE = Automatic; SWIFT_EMIT_LOC_STRINGS = YES;}; name = Debug;};
 A00000000000000000000014 = {isa = XCBuildConfiguration; buildSettings = {PRODUCT_BUNDLE_IDENTIFIER = app.teum.memo; PRODUCT_NAME = "$(TARGET_NAME)"; INFOPLIST_FILE = Teum/Info.plist; TARGETED_DEVICE_FAMILY = "1,2"; CODE_SIGN_STYLE = Automatic;}; name = Release;};
 }; rootObject = A00000000000000000000001;
}
''')
print(project)

pbx = project / "project.pbxproj"
text = pbx.read_text().replace('targets = (A00000000000000000000005);', 'targets = (A00000000000000000000005,B00000000000000000000001);')
text = text.replace('A00000000000000000000007,A00000000000000000000004);','A00000000000000000000007,B00000000000000000000004,A00000000000000000000004);')
text = text.replace('children = (A00000000000000000000008);','children = (A00000000000000000000008,B00000000000000000000005);')
objects = '''
 B00000000000000000000001 = {isa = PBXNativeTarget; buildConfigurationList = B00000000000000000000002; buildPhases = (B00000000000000000000003); buildRules = (); dependencies = (B00000000000000000000008); name = TeumTests; productName = TeumTests; productReference = B00000000000000000000005; productType = "com.apple.product-type.bundle.unit-test";};
 B00000000000000000000002 = {isa = XCConfigurationList; buildConfigurations = (B00000000000000000000006,B00000000000000000000007); defaultConfigurationIsVisible = 0; defaultConfigurationName = Debug;};
 B00000000000000000000003 = {isa = PBXSourcesBuildPhase; buildActionMask = 2147483647; files = (B0000000000000000000000A); runOnlyForDeploymentPostprocessing = 0;};
 B00000000000000000000004 = {isa = PBXFileReference; lastKnownFileType = sourcecode.swift; path = TeumTests/MemoSmokeTests.swift; sourceTree = "<group>";};
 B00000000000000000000005 = {isa = PBXFileReference; explicitFileType = wrapper.cfbundle; path = TeumTests.xctest; sourceTree = BUILT_PRODUCTS_DIR;};
 B00000000000000000000006 = {isa = XCBuildConfiguration; buildSettings = {PRODUCT_BUNDLE_IDENTIFIER = app.teum.memo.tests; PRODUCT_NAME = "$(TARGET_NAME)"; GENERATE_INFOPLIST_FILE = YES; TEST_HOST = "$(BUILT_PRODUCTS_DIR)/Teum.app/Teum"; BUNDLE_LOADER = "$(TEST_HOST)"; TARGETED_DEVICE_FAMILY = "1,2"; SWIFT_OPTIMIZATION_LEVEL = "-Onone"; CODE_SIGN_STYLE = Automatic;}; name = Debug;};
 B00000000000000000000007 = {isa = XCBuildConfiguration; buildSettings = {PRODUCT_BUNDLE_IDENTIFIER = app.teum.memo.tests; PRODUCT_NAME = "$(TARGET_NAME)"; GENERATE_INFOPLIST_FILE = YES; TEST_HOST = "$(BUILT_PRODUCTS_DIR)/Teum.app/Teum"; BUNDLE_LOADER = "$(TEST_HOST)"; TARGETED_DEVICE_FAMILY = "1,2"; CODE_SIGN_STYLE = Automatic;}; name = Release;};
 B00000000000000000000008 = {isa = PBXTargetDependency; target = A00000000000000000000005; targetProxy = B00000000000000000000009;};
 B00000000000000000000009 = {isa = PBXContainerItemProxy; containerPortal = A00000000000000000000001; proxyType = 1; remoteGlobalIDString = A00000000000000000000005; remoteInfo = Teum;};
 B0000000000000000000000A = {isa = PBXBuildFile; fileRef = B00000000000000000000004;};
'''
pbx.write_text(text.replace(' }; rootObject',objects+' }; rootObject'))
schemes = project / "xcshareddata/xcschemes"
schemes.mkdir(parents=True,exist_ok=True)
(schemes / "Teum.xcscheme").write_text('''<?xml version="1.0" encoding="UTF-8"?>
<Scheme LastUpgradeVersion="1600" version="1.3">
<BuildAction parallelizeBuildables="YES" buildImplicitDependencies="YES"><BuildActionEntries><BuildActionEntry buildForTesting="YES" buildForRunning="YES" buildForProfiling="YES" buildForArchiving="YES" buildForAnalyzing="YES"><BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="A00000000000000000000005" BuildableName="Teum.app" BlueprintName="Teum" ReferencedContainer="container:Teum.xcodeproj"/></BuildActionEntry></BuildActionEntries></BuildAction>
<TestAction buildConfiguration="Debug" shouldUseLaunchSchemeArgsEnv="YES"><Testables><TestableReference skipped="NO"><BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="B00000000000000000000001" BuildableName="TeumTests.xctest" BlueprintName="TeumTests" ReferencedContainer="container:Teum.xcodeproj"/></TestableReference></Testables></TestAction>
<LaunchAction buildConfiguration="Debug" launchStyle="0" useCustomWorkingDirectory="NO" ignoresPersistentStateOnLaunch="NO" debugDocumentVersioning="YES" allowLocationSimulation="YES"><BuildableProductRunnable runnableDebuggingMode="0"><BuildableReference BuildableIdentifier="primary" BlueprintIdentifier="A00000000000000000000005" BuildableName="Teum.app" BlueprintName="Teum" ReferencedContainer="container:Teum.xcodeproj"/></BuildableProductRunnable></LaunchAction>
<ProfileAction buildConfiguration="Release" shouldUseLaunchSchemeArgsEnv="YES"/><AnalyzeAction buildConfiguration="Debug"/><ArchiveAction buildConfiguration="Release" revealArchiveInOrganizer="YES"/>
</Scheme>''')
