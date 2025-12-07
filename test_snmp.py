import asyncio
from pysnmp.hlapi.asyncio import *

async def test_snmp():
    try:
        print("Testing SNMP query to 127.0.0.1:16161...")
        target = await UdpTransportTarget.create(('127.0.0.1', 16161), timeout=5, retries=1)
        
        errInd, errStat, errIdx, varBinds = await get_cmd(
            SnmpEngine(),
            CommunityData('public', mpModel=0),
            target,
            ContextData(),
            ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0'))
        )
        
        if errInd:
            print(f"Error Indication: {errInd}")
        elif errStat:
            print(f"Error Status: {errStat.prettyPrint()}")
        else:
            print("SUCCESS!")
            for varBind in varBinds:
                print(f"{varBind[0]} = {varBind[1]}")
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_snmp())
