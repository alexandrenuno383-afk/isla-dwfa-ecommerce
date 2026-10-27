from rest_framework import serializers


class MeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    groups = serializers.ListField(child=serializers.CharField())
