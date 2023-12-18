from django.shortcuts import render
from django.http import JsonResponse
from .models import Position  # replace with your actual model
import logging

logger = logging.getLogger(__name__)

def index(request):
    return render(request, 'index.html')

# def get_data(request):
#     data = Position.objects.all()  # or apply some filters if needed
#     data_list = list(data.values())  # convert the QuerySet to a list of dicts
#     return JsonResponse(data_list, safe=False)

def get_data(request):
    positions = Position.objects.all().values()  # Query the Position model
    logger.debug(f"Positions fetched from database: {positions}")
    positions_list = list(positions)  # Convert the QuerySet to a list
    logger.debug(f"Positions list to be sent as JSON: {positions_list}")
    return JsonResponse(positions_list, safe=False)  # Return the data as JSON
    return JsonResponse(positions_list, safe=False)  # Return the data as JSON