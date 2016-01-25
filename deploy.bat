echo "Building executable ..."
pyinstaller -y --clean joystick_gremlin.spec

echo "Building MSI installer ..."
cd dist
del /Q PFiles
del joystick_gremlin.wixobj
del joystick_gremlin.wixpdb
del joystick_gremlin.msi
candle joystick_gremlin.wxs
light -ext WixUiExtension joystick_gremlin.wixobj

@pause
