from io import BytesIO
from django.http import FileResponse, Http404
from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated

from .models import EquipmentUpload
from .serializers import UploadSerializer
from .analytics import parse_and_analyze
from .pdf_report import build_pdf


class UploadView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = UploadSerializer(data=request.data)
        if not ser.is_valid():
            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
        f = ser.validated_data['file']
        if not (f.name or '').lower().endswith('.csv'):
            return Response({'file': 'Must be a CSV file.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            rows, summary = parse_and_analyze(f)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        obj = EquipmentUpload.objects.create(
            filename=f.name,
            summary=summary,
            data=rows,
        )
        EquipmentUpload.keep_last_n(5)
        return Response({
            'id': obj.id,
            'filename': obj.filename,
            'summary': obj.summary,
            'created_at': obj.created_at.isoformat(),
        }, status=status.HTTP_201_CREATED)


class SummaryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, upload_id):
        try:
            obj = EquipmentUpload.objects.get(pk=upload_id)
        except EquipmentUpload.DoesNotExist:
            raise Http404
        return Response({
            'id': obj.id,
            'filename': obj.filename,
            'summary': obj.summary,
            'created_at': obj.created_at.isoformat(),
        })


class DataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, upload_id):
        try:
            obj = EquipmentUpload.objects.get(pk=upload_id)
        except EquipmentUpload.DoesNotExist:
            raise Http404
        return Response({'data': obj.data, 'filename': obj.filename})


class HistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = EquipmentUpload.objects.order_by('-created_at')[:5]
        out = [
            {
                'id': o.id,
                'filename': o.filename,
                'summary': o.summary,
                'created_at': o.created_at.isoformat(),
            }
            for o in qs
        ]
        return Response(out)


class ReportPdfView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, upload_id):
        try:
            obj = EquipmentUpload.objects.get(pk=upload_id)
        except EquipmentUpload.DoesNotExist:
            raise Http404
        path = build_pdf(obj)
        with open(path, 'rb') as f:
            buf = BytesIO(f.read())
        return FileResponse(
            buf,
            as_attachment=True,
            filename=f'report_{obj.filename}.pdf',
            content_type='application/pdf',
        )
