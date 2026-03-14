import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import OnlineUser, FileTransfer
from django.utils import timezone


class FileSharingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = 'file_sharing_pool'
        self.session_id = None
        self.username = None
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Remove user from online list
        if self.session_id:
            await self.remove_online_user(self.session_id)
            
            # Notify others that user left
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_left',
                    'session_id': self.session_id,
                    'username': self.username
                }
            )
            
            # Log disconnect
            print(f"User {self.username} ({self.session_id}) disconnected")
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'user_join':
            await self.handle_user_join(data)
        elif message_type == 'file_transfer_request':
            await self.handle_file_transfer_request(data)
        elif message_type == 'file_transfer_response':
            await self.handle_file_transfer_response(data)
        elif message_type == 'upload_complete':
            await self.handle_upload_complete(data)
        elif message_type == 'file_transfer_complete':
            await self.handle_file_transfer_complete(data)
        elif message_type == 'heartbeat':
            await self.handle_heartbeat()
        elif message_type == 'text_update':
            await self.handle_text_update(data)
        elif message_type == 'webrtc_offer':
            await self.handle_webrtc_offer(data)
        elif message_type == 'webrtc_answer':
            await self.handle_webrtc_answer(data)
        elif message_type == 'webrtc_ice_candidate':
            await self.handle_webrtc_ice_candidate(data)
    
    async def handle_user_join(self, data):
        self.session_id = data.get('session_id')
        self.username = data.get('username')
        
        # Add user to database
        await self.add_online_user(self.session_id, self.username)
        
        # Get all online users
        online_users = await self.get_online_users()
        
        # Send online users list to the joining user
        await self.send(text_data=json.dumps({
            'type': 'online_users',
            'users': online_users
        }))
        
        # Notify others about new user
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'session_id': self.session_id,
                'username': self.username
            }
        )
    
    async def handle_file_transfer_request(self, data):
        sender_session = data.get('sender_session')
        sender_username = data.get('sender_username')
        receiver_session = data.get('receiver_session')
        receiver_username = data.get('receiver_username')
        filename = data.get('filename')
        filesize = data.get('filesize')
        
        # Create transfer record
        transfer = await self.create_file_transfer(
            sender_session, sender_username,
            receiver_session, receiver_username,
            filename, filesize
        )
        
        # Send notification to receiver only
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'file_transfer_notification',
                'transfer_id': str(transfer.transfer_id),
                'sender_session': sender_session,
                'sender_username': sender_username,
                'receiver_session': receiver_session,
                'filename': filename,
                'filesize': filesize,
                'filesize_display': transfer.get_filesize_display()
            }
        )
    
    async def handle_file_transfer_response(self, data):
        transfer_id = data.get('transfer_id')
        accepted = data.get('accepted')
        
        # Update transfer status
        transfer = await self.update_transfer_status(
            transfer_id,
            'accepted' if accepted else 'rejected'
        )
        
        # Notify both sender and receiver
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'file_transfer_response_notification',
                'transfer_id': transfer_id,
                'accepted': accepted,
                'sender_session': transfer.sender_session,
                'receiver_session': transfer.receiver_session
            }
        )
    
    async def handle_upload_complete(self, data):
        transfer_id = data.get('transfer_id')
        
        # Get transfer to find receiver
        transfer = await self.get_transfer(transfer_id)
        
        # Notify receiver that file is ready to download
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'upload_complete_notification',
                'transfer_id': transfer_id,
                'receiver_session': transfer.receiver_session
            }
        )
    
    async def handle_file_transfer_complete(self, data):
        transfer_id = data.get('transfer_id')
        success = data.get('success')
        
        # Update transfer status
        await self.update_transfer_status(
            transfer_id,
            'completed' if success else 'failed'
        )
        
        # Notify both users
        transfer = await self.get_transfer(transfer_id)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'file_transfer_complete_notification',
                'transfer_id': transfer_id,
                'success': success,
                'sender_session': transfer.sender_session,
                'receiver_session': transfer.receiver_session
            }
        )
    
    async def handle_heartbeat(self):
        if self.session_id:
            await self.update_last_seen(self.session_id)
    
    async def handle_text_update(self, data):
        # Broadcast text update to all users
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'text_broadcast',
                'text': data.get('text', ''),
                'username': data.get('username', 'Unknown')
            }
        )
    
    async def handle_webrtc_offer(self, data):
        """Forward WebRTC offer from sender to receiver"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'webrtc_offer_notification',
                'transfer_id': data.get('transfer_id'),
                'offer': data.get('offer'),
                'sender_session': data.get('sender_session'),
                'receiver_session': data.get('receiver_session')
            }
        )
    
    async def handle_webrtc_answer(self, data):
        """Forward WebRTC answer from receiver to sender"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'webrtc_answer_notification',
                'transfer_id': data.get('transfer_id'),
                'answer': data.get('answer'),
                'sender_session': data.get('sender_session'),
                'receiver_session': data.get('receiver_session')
            }
        )
    
    async def handle_webrtc_ice_candidate(self, data):
        """Forward ICE candidate between peers"""
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'webrtc_ice_candidate_notification',
                'transfer_id': data.get('transfer_id'),
                'candidate': data.get('candidate'),
                'sender_session': data.get('sender_session'),
                'receiver_session': data.get('receiver_session'),
                'target_session': data.get('target_session')
            }
        )
    
    # WebSocket message handlers
    async def user_joined(self, event):
        # Don't send to the user who just joined
        if event['session_id'] != self.session_id:
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'session_id': event['session_id'],
                'username': event['username']
            }))
    
    async def user_left(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_left',
            'session_id': event['session_id'],
            'username': event['username']
        }))
    
    async def file_transfer_notification(self, event):
        # Only send to the receiver
        if self.session_id == event['receiver_session']:
            await self.send(text_data=json.dumps({
                'type': 'file_transfer_request',
                'transfer_id': event['transfer_id'],
                'sender_session': event['sender_session'],
                'sender_username': event['sender_username'],
                'filename': event['filename'],
                'filesize': event['filesize'],
                'filesize_display': event['filesize_display']
            }))
    
    async def file_transfer_response_notification(self, event):
        # Send to both sender and receiver
        if self.session_id in [event['sender_session'], event['receiver_session']]:
            await self.send(text_data=json.dumps({
                'type': 'file_transfer_response',
                'transfer_id': event['transfer_id'],
                'accepted': event['accepted']
            }))
    
    async def upload_complete_notification(self, event):
        # Only send to the receiver
        if self.session_id == event['receiver_session']:
            await self.send(text_data=json.dumps({
                'type': 'upload_complete',
                'transfer_id': event['transfer_id']
            }))
    
    async def file_transfer_complete_notification(self, event):
        # Send to both sender and receiver
        if self.session_id in [event['sender_session'], event['receiver_session']]:
            await self.send(text_data=json.dumps({
                'type': 'file_transfer_complete',
                'transfer_id': event['transfer_id'],
                'success': event['success']
            }))
    
    async def text_broadcast(self, event):
        # Send text update to all users except sender
        if self.username != event['username']:
            await self.send(text_data=json.dumps({
                'type': 'text_update',
                'text': event['text'],
                'username': event['username']
            }))
    
    async def webrtc_offer_notification(self, event):
        # Only send to receiver
        if self.session_id == event['receiver_session']:
            await self.send(text_data=json.dumps({
                'type': 'webrtc_offer',
                'transfer_id': event['transfer_id'],
                'offer': event['offer'],
                'sender_session': event['sender_session']
            }))
    
    async def webrtc_answer_notification(self, event):
        # Only send to sender
        if self.session_id == event['sender_session']:
            await self.send(text_data=json.dumps({
                'type': 'webrtc_answer',
                'transfer_id': event['transfer_id'],
                'answer': event['answer'],
                'receiver_session': event['receiver_session']
            }))
    
    async def webrtc_ice_candidate_notification(self, event):
        # Send to target peer
        if self.session_id == event['target_session']:
            await self.send(text_data=json.dumps({
                'type': 'webrtc_ice_candidate',
                'transfer_id': event['transfer_id'],
                'candidate': event['candidate']
            }))
    
    # Database operations
    @database_sync_to_async
    def add_online_user(self, session_id, username):
        user, created = OnlineUser.objects.get_or_create(
            session_id=session_id,
            defaults={'username': username}
        )
        if not created:
            user.username = username
            user.joined_at = timezone.now()
            user.save()
        return user
    
    @database_sync_to_async
    def remove_online_user(self, session_id):
        OnlineUser.objects.filter(session_id=session_id).delete()
    
    @database_sync_to_async
    def get_online_users(self):
        users = OnlineUser.objects.all()
        return [
            {
                'session_id': user.session_id,
                'username': user.username
            }
            for user in users
        ]
    
    @database_sync_to_async
    def update_last_seen(self, session_id):
        OnlineUser.objects.filter(session_id=session_id).update(
            last_seen=timezone.now()
        )
    
    @database_sync_to_async
    def create_file_transfer(self, sender_session, sender_username,
                            receiver_session, receiver_username,
                            filename, filesize):
        return FileTransfer.objects.create(
            sender_session=sender_session,
            sender_username=sender_username,
            receiver_session=receiver_session,
            receiver_username=receiver_username,
            filename=filename,
            filesize=filesize
        )
    
    @database_sync_to_async
    def update_transfer_status(self, transfer_id, status):
        transfer = FileTransfer.objects.get(transfer_id=transfer_id)
        transfer.status = status
        transfer.save()
        return transfer
    
    @database_sync_to_async
    def get_transfer(self, transfer_id):
        return FileTransfer.objects.get(transfer_id=transfer_id)
