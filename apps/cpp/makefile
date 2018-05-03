all:
	g++ -g -O2 -std=c++11 -pthread -march=native power-mixing.cpp -o power-mixing -lntl -lgmp -lm
clean:
	rm -f power-mixing output
test: clean all
	./power-mixing < power-mixing.input
benchmark: clean all
	./power-mixing 10 1234