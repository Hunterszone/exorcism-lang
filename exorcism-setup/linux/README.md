# How to install under Linux

## Installation Steps

1. Select a Linux folder for the download, i.e. run ```cd ~/Downloads``` in bash

2. Download the `.deb` installer from Github using 
```wget "https://github.com/Hunterszone/exorcism-lang/raw/main/exorcism-setup/linux/exorcism-installer-linux-amd64.deb"```

3. Check the downloaded executable using ```file ./exorcism-installer-linux-amd64.deb``` and ```dpkg-deb -I ./exorcism-installer-linux-amd64.deb```

4. Check which files will be put onto the system (optional) using ```dpkg-deb -c ./exorcism-installer-linux-amd64.deb```

5. Install using ```sudo apt update``` and ```sudo apt install ./exorcism-installer-linux-amd64.deb```

6. Test the installation using ```which exrc```, followed by ```exrc --version``` and ```exrc --help```

7. Then test your actual compiler:
```
mkdir ~/exorcism-test
cd ~/exorcism-test
```

8. Create a minimal `.exrc` file, using ```nano hello.exrc```, then execute ```exrc run hello.exrc```