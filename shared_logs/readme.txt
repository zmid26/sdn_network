This directory contains the logs for various testing scenarios for a 3 switch network configuration. The topology is shared as well.

1. Normal Network: 
	* The switches connect to the controller and controller sends the routing table.
2. Switch 1 Failure: 
	* The switches connect to the controller, and controller sends the routing table.
	* Switch 1 is killed.
	* Controller detects the failure and sends an updated routing table.
3. Switch 1 Failure, Restart:
	* The switches connect to the controller, and controller sends the routing table.
	* Switch 1 is killed.
	* Controller detects the failure and sends an updated routing table.
	* Switch 1 is restarted.
	* Controller detects Switch 1 is alive again and sends an updated routing table.
4. Link 1-2 Failure:
	* Switch 1 is started with the '-f 2' flag.
	* Switches connect to the controller, and controller sends the routing table.
	* Switch 1/2 detect the link failure and update the controller. 
	* Controller sends an updated routing table.
5. Link 1-2 Failure, Restart:
	* Switch 1 is started with the '-f 2' flag.
	* Switches connect to the controller, and controller sends the routing table.
	* Switch 1/2 detect the link failure and update the controller. 
	* Controller sends an updated routing table.
	* Switch 1 is killed.
	* Controller detects the failure and sends an updated routing table.
	* Switch 1 is restarted without the '-f' flag.
	* Controller detects Switch 1 is alive again and sends an updated routing table.
