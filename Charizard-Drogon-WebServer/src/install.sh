# Drogon C++ Framework

# works in Ubuntu 18.04 and Arch linux with pacman
sudo pacman -S cmake make gcc git
git clone https://github.com/drogonframework/drogon.git
cd drogon
mkdir build && cd build
cmake ..
make && sudo make install
cd ../..