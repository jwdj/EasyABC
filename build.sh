#rm reference.txt generalmidi.txt abcm2ps_osx abc2midi_osx abc2abc_osx
#rm -fr dist/EasyABC.app
python setup.py py2app
#cp -r reference.txt generalmidi.txt img locale sound dist/EasyABC.app/Contents/Resources
#cp -r bin/abcm2ps bin/abc2midi bin/abc2abc dist/EasyABC.app/Contents/Resources/bin
for file in `ls -1 locale/`; do 
   mkdir "dist/EasyABC.app/Contents/Resources/$file.lproj" 
done
mkdir "dist/EasyABC.app/Contents/Resources/English.lproj"   
#force to have executable binary as py2app remove the executable flag
chmod +x dist/EasyABC.app/Contents/Resources/bin/*
