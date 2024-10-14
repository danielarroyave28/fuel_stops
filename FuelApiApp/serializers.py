from rest_framework import serializers

class RouteInputSerializer(serializers.Serializer):
    start_city = serializers.CharField()
    start_state = serializers.CharField()
    finish_city = serializers.CharField()
    finish_state = serializers.CharField()
    
    