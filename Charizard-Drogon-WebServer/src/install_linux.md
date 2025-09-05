# Atualiza sistema
sudo pacman -Syu

# Python, FastAPI, ORM, etc.
sudo pacman -S python python-pip
pip install fastapi uvicorn sqlalchemy psycopg2-binary pydantic

# SQLite para testes (ou use PostgreSQL)
sudo pacman -S sqlite

# Drogon C++ Framework
sudo pacman -S cmake make gcc git
git clone https://github.com/drogonframework/drogon.git
cd drogon
mkdir build && cd build
cmake ..
make && sudo make install
cd ../..
