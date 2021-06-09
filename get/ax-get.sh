#! /bin/sh

# Copyright 2021 Richard Johnston <techpowerawaits@outlook.com>
# SPDX-license-identifier: 0BSD

major_ver=$1
minor_ver=$2
patch_ver=$3

check_download() {
	if [ "$1" -ne 0 ]; then
		echo "A fatal error has occured."
		echo "Unable to download file from $source"
		echo "Please ensure the major, minor, and patch version numbers are provided"
		echo
		echo "For example, running \"$0 6 0 8\" should download \"axelor-erp-v6.0.8.war\" from GitHub."
		exit 1
	fi
}

if [ "$(whoami)" != "root" ] && { [ "$1" != "--src" ] && [ "$2" != "--src" ]; }; then
	echo "A fatal error has occured."
	echo "$(whoami) is not root"
	echo "Please try again using sudo."
	exit 1
fi

if [ "$1" = "--latest" ] || [ "$2" = "--latest" ]; then
	latest_src=latest.tmp
	curl https://github.com/axelor/axelor-open-suite/releases/latest >"$latest_src"

	redirect_test=$(grep -F -o "redirected" <"$latest_src")

	if [ -n "$redirect_test" ]; then
		latest_ver=$(grep -o "[?0-9]" <"$latest_src")
		incr=0
		rm "$latest_src"

		for ver in $latest_ver; do
			incr=$((incr + 1))

			case $incr in
			1) major_ver=$ver ;;
			2) minor_ver=$ver ;;
			3) patch_ver=$ver ;;
			default) break ;;
			esac
		done
	else
		echo "A fatal error has occured."
		echo "The redirect has failed."
		exit 1
	fi
fi

version="$major_ver"."$minor_ver"."$patch_ver"
filename=axelor-erp-v"$version"
filetype="war"
src=0

if [ "$1" = "--src" ] || [ "$2" = "--src" ]; then
	src=1
	if [ "$1" != "--latest" ] && [ "$2" != "--latest" ]; then
		major_ver="$2"
		minor_ver="$3"
		patch_ver="$4"
		version="$major_ver"."$minor_ver"."$patch_ver"
		filename=axelor-erp-v"$version"
	fi

	filetype="zip"
	source=https://github.com/axelor/open-suite-webapp/archive/refs/tags/v$version.$filetype
	wget "$source" -O axelor-webapp.tmp
	check_download $?

	source=https://github.com/axelor/axelor-open-suite/archive/refs/tags/v$version.$filetype
	wget "$source" -O axelor-open-suite.tmp
	check_download $?

	unzip axelor-webapp.tmp
	mv open-suite-webapp-"$version" "$filename"-src
	unzip axelor-open-suite.tmp
	mv axelor-open-suite-"$version" "$filename"-src/modules/axelor-open-suite
	mv "$filename"-src/modules/axelor-open-suite/axelor-open-suite-"$version" "$filename"-src/modules/axelor-open-suite-"$version"
	rm -rf "$filename"-src/modules/axelor-open-suite
	mv "$filename"-src/modules/axelor-open-suite-"$version" "$filename"-src/modules/axelor-open-suite
	rm axelor-webapp.tmp
	rm axelor-open-suite.tmp
else
	source=https://github.com/axelor/open-suite-webapp/releases/download/v$version/$filename.$filetype
	wget "$source"
	check_download $?

	unzip "$filename"."$filetype" -d "$filename"
	chown -R tomcat:tomcat "$filename"
fi

branding=0

if [ -f "branding_logo.png" ]; then
	if [ "$src" -eq 1 ]; then
		cp branding_logo.png ./"$filename"-src/src/main/webapp/img/branding_logo.png
	else
		cp branding_logo.png ./"$filename"/img/branding_logo.png
		chown tomcat:tomcat ./"$filename"/img/branding_logo.png
	fi
	branding=1
fi

if [ "$branding" -eq 1 ]; then
	echo
	if [ "$src" -eq 1 ]; then
		echo "A personalized logo has been copied to ./$filename-src/src/main/webapp/img/branding_logo.png"
		echo "Please edit the \"application.logo\" entry in ./$filename-src/src/main/resources/application.properties to apply this new logo."
	else
		echo "A personalized logo has been copied to ./$filename/img/branding_logo.png"
		echo "Please edit the \"application.logo\" entry in ./$filename/WEB-INF/classes/application.properties to apply this new logo."
	fi
	echo 'Typically, the entry will be set (by default) to "img/axelor.png".'
	echo 'Simply change this to "img/branding_logo.png".'
	echo
fi

echo
if [ "$src" -eq 1 ]; then
	echo "In order to get Axelor working, the ./$filename-src/src/main/resources/application.properties file needs various database-related changes."

	# ${extracted-dir} is just an example variable and is not meant to be expanded.
	# shellcheck disable=SC2016
	echo '(If you want to get the properties file after compiling the WAR file, once extracted, it will be inside the "${extracted-dir}/WEB-INF/classes" folder.)'
else
	echo "In order to get Axelor working, the ./$filename/WEB-INF/classes/application.properties file needs various database-related changes."
fi
printf "\n\n"
echo "More specifically, the name of the database its going to use and the db user account info that owns the database needs to be entered."
echo "This script does not generate a database for you, but please ensure that no databases used for this version were used by previous versions of Axelor."
echo "This is to ensure a more reliable experience."
echo "To copy all the information from a previous instance of Axelor, please use the its built-in backup and restore feature."
printf "\n\n"
echo "If a database hasn't been created already, it is recommended to name it after the specific version number you are running."
echo "For example, axelor-$version would make a great database name."
echo "This will make life easier in case it is necessary to revert to a previous version."
echo "In that case, there would be no need to worry about conflict due to a newer version of Axelor updating the database."

if [ "$src" -eq 0 ]; then
	printf "\n\n"
	echo "In order to avoid having to specify \"$filename\" while typing in the URL or IP Address to access Axelor, please rename the folder to \"ROOT\"."
fi
