# flexfcapf
FlexFCAPF emulation evaluation repository.

The root folder contains all the code.

The folder results contains all the results files.

results/emurunoutput contains emulation output and these files are used to generate Emulation time vs Runtime graph. The python script for creating the graph is runtimeplot.py.

results/emuvssystime contains the console output of emulation run and these files are used to generate Emulation time vs Real system time difference graph. The python script for creating the graph is simemutime.py.

3_ind_conn_1000.tar.gz and 3_into_100_par_conn_1000.tar.gz contains the output delay time. The python script used to prepare delay plot graph is delayplot.py

mesh16gen_iperf_log.tar.gz, mesh16comp_iperf_log.tar.gz, mesh36comp_iperf_log.tar.gz, mesh36gen_iperf_log.tar.gz, ring36comp_iperf_log.tar.gz, and ring36gen_iperf_log.tar.gz contains the iperf client log. These files are used to create the desired data rate vs generated data rate graph and desired duration vs generated duration graph. The python script used for generating those graph is traffic_distribution.py and plotbwtimediff.py.

plotlcaused.py is used to preapere the graph of LCA used in simulation an emulation and the input for this script is sim_results_pfo_fcfs_Test_36_mesh_gen.dat and emu_results_pfo_fcfs_Test_36_mesh_gen.dat.

loadlevel.py is used to prepare the load distribution graph.

fcapf_ryu_controller.py is the Ryu SDN controller.

echoclient.py multiechoclient.py are used to test send packet between two hosts. Specifically to generate delay reports for proving data flow processing.

Test_16_mesh.dat, Test_36_mesh.dat, and Test_36_ring.dat these topology description files are used for executing all the test scenario. 

MaxiNet.cfg is an example MaxiNet.cfg file used in the testbed.
