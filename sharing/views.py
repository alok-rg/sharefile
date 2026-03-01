from django.shortcuts import render, get_object_or_404
from django.http import StreamingHttpResponse, JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import FileTransfer
import os
import tempfile
import json
import mimetypes


def index(request):
    """Main page for the file sharing application"""
    return render(request, 'sharing/index.html')


@csrf_exempt
@require_http_methods(["POST"])
def upload_file(request):
    """
    Handle file upload with streaming to avoid memory overload.
    Files are saved temporarily and streamed to receiver on demand.
    """
    try:
        transfer_id = request.POST.get('transfer_id')
        if not transfer_id:
            return JsonResponse({'error': 'Transfer ID required'}, status=400)
        
        # Get transfer record
        transfer = get_object_or_404(FileTransfer, transfer_id=transfer_id)
        
        # Check if transfer was accepted
        if transfer.status != 'accepted':
            return JsonResponse({'error': 'Transfer not accepted'}, status=400)
        
        # Get uploaded file
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return JsonResponse({'error': 'No file uploaded'}, status=400)
        
        # Create temporary directory if it doesn't exist
        temp_dir = os.path.join(tempfile.gettempdir(), 'file_share_uploads')
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save file with transfer_id as name
        file_path = os.path.join(temp_dir, str(transfer_id))
        
        # Write file in chunks to avoid memory issues
        with open(file_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks(chunk_size=8192):  # 8KB chunks
                destination.write(chunk)
        
        return JsonResponse({
            'success': True,
            'message': 'File uploaded successfully',
            'transfer_id': str(transfer_id)
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def download_file(request, transfer_id):
    """
    Stream file download to avoid loading entire file in memory.
    This allows downloading large files efficiently.
    """
    try:
        # Get transfer record
        transfer = get_object_or_404(FileTransfer, transfer_id=transfer_id)
        
        # Verify the request is from the receiver
        receiver_session = request.GET.get('session_id')
        if receiver_session != transfer.receiver_session:
            return HttpResponse('Unauthorized', status=403)
        
        # Get file path
        temp_dir = os.path.join(tempfile.gettempdir(), 'file_share_uploads')
        file_path = os.path.join(temp_dir, str(transfer_id))
        
        if not os.path.exists(file_path):
            return HttpResponse('File not found', status=404)
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(transfer.filename)
        if content_type is None:
            content_type = 'application/octet-stream'
        
        # Create streaming response
        def file_iterator(file_path, chunk_size=8192):
            """Generator to read file in chunks"""
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        
        response = StreamingHttpResponse(
            file_iterator(file_path),
            content_type=content_type
        )
        response['Content-Length'] = os.path.getsize(file_path)
        response['Content-Disposition'] = f'attachment; filename="{transfer.filename}"'
        
        return response
    
    except Exception as e:
        return HttpResponse(f'Error: {str(e)}', status=500)


@require_http_methods(["POST"])
@csrf_exempt
def cleanup_file(request, transfer_id):
    """
    Clean up temporary file after successful transfer.
    Called by receiver after download completes.
    """
    try:
        # Get transfer record
        transfer = get_object_or_404(FileTransfer, transfer_id=transfer_id)
        
        # Delete temporary file
        temp_dir = os.path.join(tempfile.gettempdir(), 'file_share_uploads')
        file_path = os.path.join(temp_dir, str(transfer_id))
        
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return JsonResponse({'success': True, 'message': 'File cleaned up'})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def get_transfer_status(request, transfer_id):
    """Get the current status of a file transfer"""
    try:
        transfer = get_object_or_404(FileTransfer, transfer_id=transfer_id)
        
        return JsonResponse({
            'transfer_id': str(transfer.transfer_id),
            'status': transfer.status,
            'filename': transfer.filename,
            'filesize': transfer.filesize,
            'filesize_display': transfer.get_filesize_display(),
            'sender_username': transfer.sender_username,
            'receiver_username': transfer.receiver_username
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=404)
