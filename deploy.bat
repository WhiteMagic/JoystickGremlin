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
"C:\Program Files (x86)\WiX Toolset v3.11\bin\candle.exe" joystick_gremlin.wxs
"C:\Program Files (x86)\WiX Toolset v3.11\bin\light.exe" -ext WixUiExtension joystick_gremlin.wixobj

@pause
