package com.example.paymentservice.service;
import com.example.paymentservice.dto.Event;
import com.example.paymentservice.domain.ProcessedEvent;
import com.example.paymentservice.repository.ProcessedEventRepository;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.UUID;
import org.springframework.amqp.AmqpRejectAndDontRequeueException;

@Service
public class PaymentService {
    @Autowired
    private ProcessedEventRepository processedEventRepository;
    @Autowired
    private RabbitTemplate rabbitTemplate;

    @Transactional
    @RabbitListener(queues = "payment.queue")
    public void processPayment(Event event) {
        if (processedEventRepository.existsById(event.getEventId())) {
            System.out.println("Event already processed: " + event.getEventId());
            return;
        }
        
        // Simulating Payment Logic...
        
        processedEventRepository.save(new ProcessedEvent(event.getEventId(), LocalDateTime.now().toString()));
        
        Event outEvent = new Event(
            UUID.randomUUID().toString(),
            "PaymentProcessed",
            LocalDateTime.now().atOffset(ZoneOffset.UTC).toString(),
            event.getAggregateId(),
            event.getPayload()
        );
        rabbitTemplate.convertAndSend("order_exchange", "payment.processed", outEvent);
    }
}