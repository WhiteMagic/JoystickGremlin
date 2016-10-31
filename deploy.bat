echo "Starting to build Gremlin ..."
C:
cd Users\Ivan Dolvich\PycharmProjects\JoystickGremlin

echo "Building executable ..."
pyinstaller -y --clean joystick_gremlin.spec

echo "Generating WIX ..."
python generate_wix.py
copy /Y joystick_gremlin.wxs dist\joystick_gremlin.wxs

echo "Building MSI installer ..."
cd dist
del /Q PFiles
del joystick_gremlin.wixobj
del joystick_gremlin.wixpdb
del joystick_gremlin.msi
candle joystick_gremlin.wxs
light -ext WixUiExtension joystick_gremlin.wixobj

@pause
