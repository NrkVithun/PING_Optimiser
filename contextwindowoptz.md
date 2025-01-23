nitial Issue:
The ping statistics were not displaying in the UI
Error: "str object has no attribute decode"
First Fix:
Fixed the string decoding issue in update_ping_stats()
Added proper handling for both bytes and string output from ping process
Second Issue:
Ping values still weren't showing up
Error in metrics handler: "not enough values to unpack"
Second Fix:
Fixed the metrics handler to properly parse ping values
Added handling for 'ms' suffix
Improved value conversion to float
Current State:
Metrics are being logged correctly (we can see this in the logs)
But UI values still aren't displaying