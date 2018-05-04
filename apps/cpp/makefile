all:
	g++ -g -O2 -std=c++17 -pthread -march=native power-mixing.cpp -o power-mixing -lntl -lgmp -lm
clean:
	rm -f power-mixing output powers.sum
test: clean all
	./power-mixing power-mixing.input
benchmark: all
	./power-mixing 10 1234