#SeduceBoard


## SNMP Walk

```
# Display OIDs as named function
snmpwalk -O f -m ~/Downloads/powernet421.mib -cpublic 10.44.193.141
# Display OID as numbers
snmpwalk -O n -m ~/Downloads/powernet421.mib -cpublic 10.44.193.141
```