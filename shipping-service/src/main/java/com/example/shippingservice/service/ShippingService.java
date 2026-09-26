package com.example.shippingservice.service;
import com.example.shippingservice.dto.Event;
import com.example.shippingservice.domain.ProcessedEvent;
import com.example.shippingservice.repository.ProcessedEventRepository;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.UUID;

@Service
public class ShippingService {
    @Autowired
    private ProcessedEventRepository processedEventRepository;
    @Autowired
    private RabbitTemplate rabbitTemplate;

    @Transactional
    @RabbitListener(queues = "shipping.queue")
    public void processShipping(Event event) {
        if (processedEventRepository.existsById(event.getEventId())) {
            System.out.println("Event already processed: " + event.getEventId());
            return;
        }
        
        processedEventRepository.save(new ProcessedEvent(event.getEventId(), LocalDateTime.now().toString()));
        
        Event outEvent = new Event(
            UUID.randomUUID().toString(),
            "ShipmentCreated",
            LocalDateTime.now().atOffset(ZoneOffset.UTC).toString(),
            event.getAggregateId(),
            event.getPayload()
        );
        rabbitTemplate.convertAndSend("order_exchange", "shipment.created", outEvent);
    }
}