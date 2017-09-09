
cp -r dist/deb_package tmp/

dpkg --build /tmp/deb_package easyabc-1.3.7.deb
