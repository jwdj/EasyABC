rm "dist/EasyABC_1.3.7.dmg"
hdiutil create "dist/EasyABC_1.3.7.dmg" -volname "EasyABC 1.3.7" -fs HFS+ -srcfolder "dist/EasyABC.app"
