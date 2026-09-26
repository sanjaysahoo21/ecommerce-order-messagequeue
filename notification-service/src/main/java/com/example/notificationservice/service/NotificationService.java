package com.example.notificationservice.service;
import com.example.notificationservice.dto.Event;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Service;

@Service
public class NotificationService {
    @RabbitListener(queues = "notification.queue")
    public void processNotification(Event event) {
        System.out.println(String.format("Notification sent for event: %s, Order ID: %s", 
            event.getEventType(), event.getAggregateId()));
    }
}