import solver
k = 32
p = 
dc_sums = [k for i in range(k)]
print(solver.solve(dc_sums))






def load_input_from_file(k,p):

	filename = "powers.sum" 
	
	FD = open(filename, "r")
	line = FD.readline()
	if int(line) != p:
		print "p dismatch!! p in file is %d"%(int(line))
	line = FD.readline()
	if int(line) != k:
		print "k dismatch!! k in file is %d"%(int(line))


	line = FD.readline()
	i = 0
	while line and i < self.k:
		#print i
		self.inputs[i] = Share(self.runtime,self.Zp,self.Zp(int(line)))

		line = FD.readline()  
		i = i + 1
