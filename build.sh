#rm reference.txt generalmidi.txt abcm2ps_osx abc2midi_osx abc2abc_osx
#rm -fr dist/EasyABC.app
python setup.py py2app
#cp -r reference.txt generalmidi.txt img locale sound dist/EasyABC.app/Contents/Resources
#cp -r bin/abcm2ps bin/abc2midi bin/abc2abc dist/EasyABC.app/Contents/Resources/bin
for file in `ls -1 locale/`; do 
   mkdir "dist/EasyABC.app/Contents/Resources/$file.lproj" 
done
mkdir "dist/EasyABC.app/Contents/Resources/English.lproj"   

#FAU 20240103: there shall be no executable within Resources folder. Need to move them to Helpers or MacOS

mkdir dist/EasyABC.app/Contents/Helpers
cp bin/* dist/EasyABC.app/Contents/Helpers

#FAU 20240105: Ghostscript library introduced directly by py2app doesn't seem to work thus force addition manually after build
cp mac_libs_gs/*.dylib dist/EasyABC.app/Contents/Frameworks
