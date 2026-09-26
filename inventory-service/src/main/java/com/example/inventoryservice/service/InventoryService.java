package com.example.inventoryservice.service;
import com.example.inventoryservice.dto.Event;
import com.example.inventoryservice.domain.ProcessedEvent;
import com.example.inventoryservice.repository.ProcessedEventRepository;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.UUID;
import org.springframework.amqp.AmqpRejectAndDontRequeueException;
import java.util.List;
import java.util.Map;

@Service
public class InventoryService {
    @Autowired
    private ProcessedEventRepository processedEventRepository;
    @Autowired
    private RabbitTemplate rabbitTemplate;

    @Transactional
    @RabbitListener(queues = "inventory.queue")
    public void processInventory(Event event) {
        if (processedEventRepository.existsById(event.getEventId())) {
            System.out.println("Event already processed: " + event.getEventId());
            return;
        }
        
        // Trigger DLQ for specific productId
        List<Map<String, Object>> items = (List<Map<String, Object>>) event.getPayload().get("items");
        if (items != null) {
            for (Map<String, Object> item : items) {
                if ("FAIL-ME".equals(item.get("productId"))) {
                    throw new AmqpRejectAndDontRequeueException("Simulating failure for DLQ");
                }
            }
        }
        
        processedEventRepository.save(new ProcessedEvent(event.getEventId(), LocalDateTime.now().toString()));
        
        Event outEvent = new Event(
            UUID.randomUUID().toString(),
            "InventoryReserved",
            LocalDateTime.now().atOffset(ZoneOffset.UTC).toString(),
            event.getAggregateId(),
            event.getPayload()
        );
        rabbitTemplate.convertAndSend("order_exchange", "inventory.reserved", outEvent);
    }
}