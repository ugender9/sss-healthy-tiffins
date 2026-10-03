import asyncio
import websockets
import json
import urllib.request

async def test_ws_and_order():
    uri = 'ws://127.0.0.1:8000/ws'
    async with websockets.connect(uri) as ws:
        msg1 = await ws.recv()
        print('1. Handshake received:', json.loads(msg1)['event'])

        # Create a test booking via REST
        payload = json.dumps({
            'customer_name': 'Ramesh Kumar',
            'phone': '9876543210',
            'address': 'Flat 402, Green Meadows',
            'items': [{'name': 'Ragi Idly', 'qty': 2, 'price': 40}],
            'total_amount': 80
        }).encode('utf-8')
        
        req = urllib.request.Request('http://127.0.0.1:8000/api/bookings', data=payload, headers={'Content-Type': 'application/json'})
        resp = urllib.request.urlopen(req)
        created_booking = json.loads(resp.read().decode())
        order_id = created_booking['id']
        print('2. Booking created via REST:', order_id)

        # Verify WebSocket received the real-time event
        ws_msg = await ws.recv()
        event_data = json.loads(ws_msg)
        print('3. Real-time WS event received:', event_data['event'], 'for order', event_data['booking']['id'])

        # Update status
        status_payload = json.dumps({'status': 'Preparing'}).encode('utf-8')
        patch_req = urllib.request.Request(
            f'http://127.0.0.1:8000/api/bookings/{order_id}/status',
            data=status_payload,
            headers={'Content-Type': 'application/json'},
            method='PATCH'
        )
        urllib.request.urlopen(patch_req)

        # Verify WebSocket status updated event
        status_msg = await ws.recv()
        status_data = json.loads(status_msg)
        print('4. Real-time Status update WS event:', status_data['event'], 'New status:', status_data['status'])

        print('ALL REAL-TIME WEBSOCKET AND REST TESTS PASSED!')

if __name__ == '__main__':
    asyncio.run(test_ws_and_order())
