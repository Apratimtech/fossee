from rest_framework import serializers


class UploadSerializer(serializers.Serializer):
    file = serializers.FileField(help_text='CSV file with Equipment Name, Type, Flowrate, Pressure, Temperature')
