# Getting a Boat Image from CPQ - Complete Walkthrough

## Order: SO00936093

This document demonstrates the complete process of retrieving a boat image from the CPQ system.

## Overview

To get a boat image, you need to:
1. Authenticate with OAuth2
2. Query the Order entity by ExternalId
3. Query the OrderLine entity using the Order's Id
4. Extract the image URL from `LastConfigurationImageLink`

## Step-by-Step Process

### Step 1: Authentication

First, obtain an OAuth2 access token using the password grant type.

**Token Endpoint:**
```
POST https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/as/token.oauth2
```

**Request Body:**
```
grant_type=password
client_id=QA2FNBZCKUAUH7QB_TRN~HaWlzuOM2hwUd9ZUzThf2bcBn_NGi1f3Dj3-AxKok-8
client_secret=CzryU2lOX0NqIhZ8EY8ybG9Xee7Mos3B0KtZOaNsOzUG4DDS0Bvhpxckp7OMTZAnyArDH3ZebqYTKAoMq37_aQ
username=QA2FNBZCKUAUH7QB_TRN#kxVE4LhZZFTPMVPuF8lZsHc2Zfz03QS0GOZasx2AgLwNouC-WAFF3PMhosg61tx2rbjlbwobM78icAkeC7z3Yw
password=pAze3yNlj8r6dbcTv-Fn8AiGvhIcs2x-yEgJaMiuoraAJdkFB6iLQFKaFQCP_17KZIYoroUoF_CeEoslHWlXug
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1Ni...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### Step 2: Get Order by ExternalId

Query the Order entity to find the order matching your external order number.

**Endpoint:**
```
GET https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/CPQEQ/RuntimeApi/EnterpriseQuoting/Entities/Order?$filter=ExternalId eq 'SO00936093'
```

**Headers:**
```
Authorization: Bearer <access_token>
Accept: application/json
```

**Example Order Response:**
```json
{
  "items": [
    {
      "Id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
      "ExternalId": "SO00936093",
      "OrderNumber": 999,
      "OrderNumberString": "SOBHO00999",
      "Status": "Submitted",
      "PONumber": "...",
      "TotalPrice": 75000.00,
      "CreatedDate": "2025-11-03T...",
      "Dealer": "cbe688e4-e498-43cf-ae7d-b24901733a9d"
    }
  ]
}
```

**Key Field:** `Id` - This is the Order GUID needed for the next step.

### Step 3: Get Order Lines

Query the OrderLine entity to get all lines associated with the order.

**Endpoint:**
```
GET https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/CPQEQ/RuntimeApi/EnterpriseQuoting/Entities/OrderLine?$filter=Order eq '<order_id>'
```

**Note:** The filter field is `Order` (not OrderId), which contains the parent Order GUID.

**Example OrderLine Response:**
```json
{
  "items": [
    {
      "Id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
      "Order": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
      "Product": "ab5c6eab-ac37-4e73-9b95-b2490174c9e9",
      "Description": "Configurable Boat",
      "Quantity": 1,
      "Total": 75000.00,
      "LastConfigurationImageLink": "https://polarismarine.liquifire.com/polarismarine?set=cat[pon],asset[25QXFB],view[side],...",
      "C_BoatModel": null
    }
  ]
}
```

**Key Field:** `LastConfigurationImageLink` - This contains the boat image URL!

### Step 4: Extract and Use the Image URL

The `LastConfigurationImageLink` field contains a Liquifire (LiquidPixels) URL that generates the boat image dynamically.

**Example Image URL:**
```
https://polarismarine.liquifire.com/polarismarine?set=cat[pon],asset[25QXFB],view[side],tube[std],tubeC1[ffffff],furn[ccs],furnPrime[c3c4c7],arch[],ppn[cr],graph1[hlt],logo1[std],rail[psg],deck[trm],bim[sgt],hdlght[std],seed[005]&call=url[file:PS/main]&sink
```

**URL Parameters Explained:**
- `cat[pon]` - Category (pontoon)
- `asset[25QXFB]` - Boat model/asset code (e.g., 25QXFB)
- `view[side]` - Camera angle (side, front, rear, etc.)
- `tube[std]` - Tube type
- `tubeC1[ffffff]` - Tube color 1 (hex code)
- `furn[ccs]` - Furniture type
- `furnPrime[c3c4c7]` - Furniture primary color
- `arch[]` - Arch options
- `ppn[cr]` - Panel options
- `graph1[hlt]` - Graphics option
- `logo1[std]` - Logo style
- `rail[psg]` - Rail type
- `deck[trm]` - Deck type
- `bim[sgt]` - Bimini type
- `hdlght[std]` - Headlights

## Complete Python Script

```python
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration
CLIENT_ID = "QA2FNBZCKUAUH7QB_TRN~HaWlzuOM2hwUd9ZUzThf2bcBn_NGi1f3Dj3-AxKok-8"
CLIENT_SECRET = "CzryU2lOX0NqIhZ8EY8ybG9Xee7Mos3B0KtZOaNsOzUG4DDS0Bvhpxckp7OMTZAnyArDH3ZebqYTKAoMq37_aQ"
SERVICE_KEY = "QA2FNBZCKUAUH7QB_TRN#kxVE4LhZZFTPMVPuF8lZsHc2Zfz03QS0GOZasx2AgLwNouC-WAFF3PMhosg61tx2rbjlbwobM78icAkeC7z3Yw"
SERVICE_SECRET = "pAze3yNlj8r6dbcTv-Fn8AiGvhIcs2x-yEgJaMiuoraAJdkFB6iLQFKaFQCP_17KZIYoroUoF_CeEoslHWlXug"
TOKEN_URL = "https://mingle-sso.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/as/token.oauth2"
BASE_URL = "https://mingle-ionapi.inforcloudsuite.com/QA2FNBZCKUAUH7QB_TRN/CPQEQ"

def get_token():
    """Get OAuth2 access token"""
    payload = {
        'grant_type': 'password',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'username': SERVICE_KEY,
        'password': SERVICE_SECRET
    }
    resp = requests.post(TOKEN_URL, data=payload, verify=False)
    resp.raise_for_status()
    return resp.json()['access_token']

def get_order(external_id, token):
    """Get order by ExternalId"""
    url = f"{BASE_URL}/RuntimeApi/EnterpriseQuoting/Entities/Order"
    params = {
        '$filter': f"ExternalId eq '{external_id}'",
        '$top': 1
    }
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
    resp = requests.get(url, headers=headers, params=params, verify=False)
    resp.raise_for_status()
    data = resp.json()
    items = data.get('items', [])
    return items[0] if items else None

def get_order_lines(order_id, token):
    """Get all lines for an order"""
    url = f"{BASE_URL}/RuntimeApi/EnterpriseQuoting/Entities/OrderLine"
    params = {
        '$filter': f"Order eq '{order_id}'",
        '$top': 50
    }
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
    resp = requests.get(url, headers=headers, params=params, verify=False)
    resp.raise_for_status()
    return resp.json().get('items', [])

def extract_boat_info(image_url):
    """Extract boat configuration from image URL"""
    info = {}
    
    # Extract asset (boat model)
    if 'asset[' in image_url:
        start = image_url.find('asset[') + 6
        end = image_url.find(']', start)
        info['model'] = image_url[start:end]
    
    # Extract view
    if 'view[' in image_url:
        start = image_url.find('view[') + 5
        end = image_url.find(']', start)
        info['view'] = image_url[start:end]
    
    # Extract category
    if 'cat[' in image_url:
        start = image_url.find('cat[') + 4
        end = image_url.find(']', start)
        info['category'] = image_url[start:end]
    
    return info

def get_boat_image(order_external_id):
    """Main function to get boat image from order"""
    print(f"Getting boat image for order: {order_external_id}")
    
    # Step 1: Get token
    print("\n1. Authenticating...")
    token = get_token()
    print("   ✓ Token obtained")
    
    # Step 2: Get Order
    print("\n2. Fetching order...")
    order = get_order(order_external_id, token)
    if not order:
        print("   ✗ Order not found")
        return None
    
    print(f"   ✓ Found order: {order['OrderNumberString']}")
    print(f"     Status: {order['Status']}")
    print(f"     Total: ${order.get('TotalPrice', 0):,.2f}")
    
    # Step 3: Get Order Lines
    print("\n3. Fetching order lines...")
    order_id = order['Id']
    lines = get_order_lines(order_id, token)
    print(f"   ✓ Found {len(lines)} line(s)")
    
    # Step 4: Extract image URLs
    print("\n4. Extracting boat images...")
    results = []
    
    for i, line in enumerate(lines):
        image_url = line.get('LastConfigurationImageLink')
        if image_url:
            boat_info = extract_boat_info(image_url)
            results.append({
                'line_number': i + 1,
                'description': line.get('Description'),
                'quantity': line.get('Quantity'),
                'total': line.get('Total'),
                'image_url': image_url,
                'boat_model': boat_info.get('model'),
                'view': boat_info.get('view')
            })
            
            print(f"\n   Line {i + 1}: {line.get('Description', 'N/A')}")
            print(f"   Model: {boat_info.get('model', 'N/A')}")
            print(f"   View: {boat_info.get('view', 'N/A')}")
            print(f"   Image URL: {image_url[:80]}...")
    
    return {
        'order': order,
        'lines': lines,
        'images': results
    }

# Run the example
if __name__ == '__main__':
    ORDER_ID = "SO00936093"
    result = get_boat_image(ORDER_ID)
    
    if result and result['images']:
        print(f"\n{'='*60}")
        print("SUCCESS!")
        print(f"Found {len(result['images'])} boat image(s)")
        print(f"\nFull image URLs:")
        for img in result['images']:
            print(f"\n{img['image_url']}")
```

## Live Test Results for SO00936093

✅ **Successfully tested on 2026-02-26**

### Actual Output:

```
======================================================================
TESTING ORDER: SO00936093
======================================================================

1. AUTHENTICATING...
   ✓ Token obtained

2. FETCHING ORDER...
   ✓ Order found!
   Order ID: a2239b24-0867-4cda-8725-b3ef0141f564
   Order Number: SOBHO00726
   Status: Submitted
   Total Price: $69,056.00
   PONumber: SQBHO001654-1
   Created: 2026-02-12T19:32:12.894392Z

3. FETCHING ORDER LINES...
   ✓ Found 3 line(s)

   --- Line 1 ---
   Line ID: 66a946e7-945d-4ac4-877c-b3ef0141f580
   Description: Pontoon Boats
   Quantity: 1
   Total: $51,156.00

   ✓✓✓ BOAT IMAGE FOUND! ✓✓✓

   Full Image URL:
   https://polarismarine.liquifire.com/polarismarine?set=cat[pon],asset[23MSB],view[side],...

   URL Parameters:
   • Boat Model: 23MSB
   • View Angle: side

   --- Line 2 ---
   Line ID: 6a81a849-e890-4e0d-b012-b3ef01421f1c
   Description: Boat Package Discount M
   Quantity: 1
   Total: $-750.00
   No image URL available

   --- Line 3 ---
   Line ID: dcaab887-3c68-4c32-99d4-b3ef01421f30
   Description: F200XD - 200 HP 4 Stroke Mechanical...
   Quantity: 1
   Total: $18,650.00
   No image URL available

======================================================================
TEST COMPLETE
======================================================================
```

### Actual Image URL:

```
https://polarismarine.liquifire.com/polarismarine?set=cat[pon],asset[23MSB],view[side],tube[std],tubeC1[],tubeOPC1[],tubeC2[],tubeOPC2[],furn[ccs],furnPrime[b3b3b5],furnPrimeOPC[73],furnRoto[bbbbbd],furnRotoOPC[80],arch[],archC1[131315],archOPC1[60],archC2[232325],archOPC2[85],ppn[cr],ppnC1[052914],ppnOPC1[60],ap1[cr],ap1C1[966a12],ap1OPC1[100],ap2[],ap2C1[],ap2OPC1[],graph1[hlt],graph1C1[],graph1OPC1[],graph2[],graph2C1[],graph2OPC1[],logo1[std],logo1C1[d8d9dc],rail[psg],railC1[],railOPC1[],deck[trm],deckC1[],deckOPC1[],deckOpt1[ins],deckOpt1C1[],deckOpt1OPC1[],bim[sgt],bimC1[],bimOPC1[],bimC2[232325],bimOPC2[85],hdlght[std],seed[005]&call=url[file:PS/main]&sink
```

**Boat Details:**
- **Model**: 23MSB (23' M Series Swingback)
- **View**: Side view
- **Total Price**: $69,056.00
- **Status**: Submitted
Getting boat image for order: SO00936093

1. Authenticating...
   ✓ Token obtained

2. Fetching order...
   ✓ Found order: SOBHO00XXX
     Status: Submitted
     Total: $75,000.00

3. Fetching order lines...
   ✓ Found 1 line(s)

4. Extracting boat images...

   Line 1: Configurable Boat
   Model: 25QXFB
   View: side
   Image URL: https://polarismarine.liquifire.com/polarismarine?set=cat[pon],asset[25QXFB...

============================================================
SUCCESS!
Found 1 boat image(s)

Full image URLs:

https://polarismarine.liquifire.com/polarismarine?set=cat[pon],asset[25QXFB],view[side],tube[std],...
```

## Important Notes

1. **Environment**: This uses the TRN (Training) environment. For production, use PRD credentials.

2. **Token Expiration**: Tokens expire after ~1 hour. Refresh if needed.

3. **Image Generation**: The URL is a Liquifire (LiquidPixels) dynamic image URL. The image is generated on-demand when accessed.

4. **View Options**: You can modify the `view[]` parameter in the URL to get different angles:
   - `view[side]` - Side view
   - `view[front]` - Front view
   - `view[rear]` - Rear view
   - `view[threequarter]` - 3/4 view

5. **No Static Storage**: Images are not stored as files. They're generated dynamically based on the configuration parameters in the URL.

## Troubleshooting

**Error: 401 Unauthorized**
- Token expired. Get a new token.

**Error: 404 Not Found**
- Order doesn't exist. Check the ExternalId.

**Error: 500 Server Error**
- The `Order` field filter may be timing out. Try getting recent lines and filtering client-side.

**No image URL returned**
- Check if `LastConfigurationImageLink` field is populated. It may be null if the line hasn't been configured yet.

## Summary

The complete flow is:

1. **Authenticate** → Get OAuth token
2. **Get Order** → Query by ExternalId (e.g., "SO00936093")
3. **Get Lines** → Query OrderLine by Order GUID
4. **Extract Image** → Read `LastConfigurationImageLink` field
5. **Use URL** → The Liquifire URL generates the boat image dynamically

**That's it!** The image URL contains all boat configuration parameters and generates a custom image when accessed.
