import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip())

# Common Event Class (duplicated across services to keep them independent)
def get_event_class(pkg):
    return f"""
package com.example.{pkg}.dto;

import java.util.Map;

public class Event {{
    private String eventId;
    private String eventType;
    private String timestamp;
    private String aggregateId;
    private Map<String, Object> payload;

    public Event() {{}}

    public Event(String eventId, String eventType, String timestamp, String aggregateId, Map<String, Object> payload) {{
        this.eventId = eventId;
        this.eventType = eventType;
        this.timestamp = timestamp;
        this.aggregateId = aggregateId;
        this.payload = payload;
    }}

    public String getEventId() {{ return eventId; }}
    public void setEventId(String eventId) {{ this.eventId = eventId; }}
    public String getEventType() {{ return eventType; }}
    public void setEventType(String eventType) {{ this.eventType = eventType; }}
    public String getTimestamp() {{ return timestamp; }}
    public void setTimestamp(String timestamp) {{ this.timestamp = timestamp; }}
    public String getAggregateId() {{ return aggregateId; }}
    public void setAggregateId(String aggregateId) {{ this.aggregateId = aggregateId; }}
    public Map<String, Object> getPayload() {{ return payload; }}
    public void setPayload(Map<String, Object> payload) {{ this.payload = payload; }}
}}
"""

def get_processed_event_class(pkg):
    return f"""
package com.example.{pkg}.domain;

import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

@Entity
@Table(name = "processed_events")
public class ProcessedEvent {{
    @Id
    private String eventId;
    private String processedAt;

    public ProcessedEvent() {{}}
    public ProcessedEvent(String eventId, String processedAt) {{
        this.eventId = eventId;
        this.processedAt = processedAt;
    }}
    public String getEventId() {{ return eventId; }}
    public void setEventId(String eventId) {{ this.eventId = eventId; }}
    public String getProcessedAt() {{ return processedAt; }}
    public void setProcessedAt(String processedAt) {{ this.processedAt = processedAt; }}
}}
"""

def get_processed_event_repo(pkg):
    return f"""
package com.example.{pkg}.repository;

import com.example.{pkg}.domain.ProcessedEvent;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface ProcessedEventRepository extends JpaRepository<ProcessedEvent, String> {{
}}
"""

# ORDER SERVICE
pkg = "orderservice"
base = f"order-service/src/main/java/com/example/{pkg}"

write_file(f"{base}/dto/Event.java", get_event_class(pkg))

write_file(f"{base}/domain/Order.java", f"""
package com.example.{pkg}.domain;
import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "orders")
public class Order {{
    @Id
    private String id;
    @Column(columnDefinition = "TEXT")
    private String items;
    private BigDecimal totalPrice;
    private String status;
    private LocalDateTime createdAt;
    
    // Getters and Setters
    public String getId() {{ return id; }}
    public void setId(String id) {{ this.id = id; }}
    public String getItems() {{ return items; }}
    public void setItems(String items) {{ this.items = items; }}
    public BigDecimal getTotalPrice() {{ return totalPrice; }}
    public void setTotalPrice(BigDecimal totalPrice) {{ this.totalPrice = totalPrice; }}
    public String getStatus() {{ return status; }}
    public void setStatus(String status) {{ this.status = status; }}
    public LocalDateTime getCreatedAt() {{ return createdAt; }}
    public void setCreatedAt(LocalDateTime createdAt) {{ this.createdAt = createdAt; }}
}}
""")

write_file(f"{base}/repository/OrderRepository.java", f"""
package com.example.{pkg}.repository;
import com.example.{pkg}.domain.Order;
import org.springframework.data.jpa.repository.JpaRepository;
public interface OrderRepository extends JpaRepository<Order, String> {{}}
""")

write_file(f"{base}/config/RabbitMQConfig.java", f"""
package com.example.{pkg}.config;
import org.springframework.amqp.core.*;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitMQConfig {{
    public static final String EXCHANGE = "order_exchange";
    public static final String QUEUE_ORDER_CREATED = "order.created.queue";
    
    @Bean
    public TopicExchange exchange() {{ return new TopicExchange(EXCHANGE, true, false); }}
    
    @Bean
    public Queue orderCreatedQueue() {{ return new Queue(QUEUE_ORDER_CREATED, true); }}
    
    @Bean
    public Binding bindingOrderCreated() {{ return BindingBuilder.bind(orderCreatedQueue()).to(exchange()).with("order.created"); }}
    
    // Queues to listen for status updates
    @Bean
    public Queue paymentProcessedStatusQueue() {{ return new Queue("order.status.payment.queue", true); }}
    @Bean
    public Binding bindingPaymentStatus() {{ return BindingBuilder.bind(paymentProcessedStatusQueue()).to(exchange()).with("payment.processed"); }}
    
    @Bean
    public Queue inventoryReservedStatusQueue() {{ return new Queue("order.status.inventory.queue", true); }}
    @Bean
    public Binding bindingInventoryStatus() {{ return BindingBuilder.bind(inventoryReservedStatusQueue()).to(exchange()).with("inventory.reserved"); }}
    
    @Bean
    public Queue shipmentCreatedStatusQueue() {{ return new Queue("order.status.shipment.queue", true); }}
    @Bean
    public Binding bindingShipmentStatus() {{ return BindingBuilder.bind(shipmentCreatedStatusQueue()).to(exchange()).with("shipment.created"); }}
    
    @Bean
    public MessageConverter converter() {{ return new Jackson2JsonMessageConverter(); }}
}}
""")

write_file(f"{base}/controller/OrderController.java", f"""
package com.example.{pkg}.controller;
import com.example.{pkg}.domain.Order;
import com.example.{pkg}.repository.OrderRepository;
import com.example.{pkg}.dto.Event;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.Map;
import java.util.UUID;
import com.fasterxml.jackson.databind.ObjectMapper;

@RestController
@RequestMapping("/api/orders")
public class OrderController {{
    @Autowired
    private OrderRepository orderRepository;
    @Autowired
    private RabbitTemplate rabbitTemplate;
    @Autowired
    private ObjectMapper objectMapper;

    @PostMapping
    public ResponseEntity<Map<String, String>> createOrder(@RequestBody Map<String, Object> request) throws Exception {{
        String orderId = UUID.randomUUID().toString();
        Order order = new Order();
        order.setId(orderId);
        order.setItems(objectMapper.writeValueAsString(request.get("items")));
        order.setTotalPrice(new BigDecimal(request.get("totalPrice").toString()));
        order.setStatus("PENDING");
        order.setCreatedAt(LocalDateTime.now());
        orderRepository.save(order);

        Event event = new Event(
            UUID.randomUUID().toString(),
            "OrderCreated",
            LocalDateTime.now().atOffset(ZoneOffset.UTC).toString(),
            orderId,
            request
        );
        rabbitTemplate.convertAndSend("order_exchange", "order.created", event);

        return ResponseEntity.accepted().body(Map.of("orderId", orderId));
    }}

    @GetMapping("/{{id}}")
    public ResponseEntity<?> getOrder(@PathVariable String id) {{
        return orderRepository.findById(id)
                .map(order -> ResponseEntity.ok(order))
                .orElse(ResponseEntity.notFound().build());
    }}
}}
""")

write_file(f"{base}/service/OrderConsumerService.java", f"""
package com.example.{pkg}.service;
import com.example.{pkg}.domain.Order;
import com.example.{pkg}.repository.OrderRepository;
import com.example.{pkg}.dto.Event;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class OrderConsumerService {{
    @Autowired
    private OrderRepository orderRepository;

    @RabbitListener(queues = "order.status.payment.queue")
    public void onPaymentProcessed(Event event) {{
        updateOrderStatus(event.getAggregateId(), "PAID");
    }}
    
    @RabbitListener(queues = "order.status.inventory.queue")
    public void onInventoryReserved(Event event) {{
        updateOrderStatus(event.getAggregateId(), "INVENTORY_RESERVED");
    }}
    
    @RabbitListener(queues = "order.status.shipment.queue")
    public void onShipmentCreated(Event event) {{
        updateOrderStatus(event.getAggregateId(), "SHIPPED");
    }}
    
    private void updateOrderStatus(String orderId, String status) {{
        orderRepository.findById(orderId).ifPresent(order -> {{
            order.setStatus(status);
            orderRepository.save(order);
        }});
    }}
}}
""")


# PAYMENT SERVICE
pkg = "paymentservice"
base = f"payment-service/src/main/java/com/example/{pkg}"
write_file(f"{base}/dto/Event.java", get_event_class(pkg))
write_file(f"{base}/domain/ProcessedEvent.java", get_processed_event_class(pkg))
write_file(f"{base}/repository/ProcessedEventRepository.java", get_processed_event_repo(pkg))

write_file(f"{base}/config/RabbitMQConfig.java", f"""
package com.example.{pkg}.config;
import org.springframework.amqp.core.*;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitMQConfig {{
    @Bean
    public TopicExchange exchange() {{ return new TopicExchange("order_exchange", true, false); }}
    @Bean
    public Queue paymentQueue() {{ return new Queue("payment.queue", true); }}
    @Bean
    public Binding binding() {{ return BindingBuilder.bind(paymentQueue()).to(exchange()).with("order.created"); }}
    @Bean
    public MessageConverter converter() {{ return new Jackson2JsonMessageConverter(); }}
}}
""")

write_file(f"{base}/service/PaymentService.java", f"""
package com.example.{pkg}.service;
import com.example.{pkg}.dto.Event;
import com.example.{pkg}.domain.ProcessedEvent;
import com.example.{pkg}.repository.ProcessedEventRepository;
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
public class PaymentService {{
    @Autowired
    private ProcessedEventRepository processedEventRepository;
    @Autowired
    private RabbitTemplate rabbitTemplate;

    @Transactional
    @RabbitListener(queues = "payment.queue")
    public void processPayment(Event event) {{
        if (processedEventRepository.existsById(event.getEventId())) {{
            System.out.println("Event already processed: " + event.getEventId());
            return;
        }}
        
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
    }}
}}
""")


# INVENTORY SERVICE
pkg = "inventoryservice"
base = f"inventory-service/src/main/java/com/example/{pkg}"
write_file(f"{base}/dto/Event.java", get_event_class(pkg))
write_file(f"{base}/domain/ProcessedEvent.java", get_processed_event_class(pkg))
write_file(f"{base}/repository/ProcessedEventRepository.java", get_processed_event_repo(pkg))

write_file(f"{base}/config/RabbitMQConfig.java", f"""
package com.example.{pkg}.config;
import org.springframework.amqp.core.*;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitMQConfig {{
    @Bean
    public TopicExchange exchange() {{ return new TopicExchange("order_exchange", true, false); }}
    
    @Bean
    public TopicExchange dlx() {{ return new TopicExchange("dlx_exchange", true, false); }}
    
    @Bean
    public Queue dlq() {{ return new Queue("inventory.dlq", true); }}
    
    @Bean
    public Binding dlqBinding() {{ return BindingBuilder.bind(dlq()).to(dlx()).with("inventory.dlq.key"); }}
    
    @Bean
    public Queue inventoryQueue() {{ 
        return QueueBuilder.durable("inventory.queue")
                           .withArgument("x-dead-letter-exchange", "dlx_exchange")
                           .withArgument("x-dead-letter-routing-key", "inventory.dlq.key")
                           .build(); 
    }}
    
    @Bean
    public Binding binding() {{ return BindingBuilder.bind(inventoryQueue()).to(exchange()).with("payment.processed"); }}
    @Bean
    public MessageConverter converter() {{ return new Jackson2JsonMessageConverter(); }}
}}
""")

write_file(f"{base}/service/InventoryService.java", f"""
package com.example.{pkg}.service;
import com.example.{pkg}.dto.Event;
import com.example.{pkg}.domain.ProcessedEvent;
import com.example.{pkg}.repository.ProcessedEventRepository;
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
public class InventoryService {{
    @Autowired
    private ProcessedEventRepository processedEventRepository;
    @Autowired
    private RabbitTemplate rabbitTemplate;

    @Transactional
    @RabbitListener(queues = "inventory.queue")
    public void processInventory(Event event) {{
        if (processedEventRepository.existsById(event.getEventId())) {{
            System.out.println("Event already processed: " + event.getEventId());
            return;
        }}
        
        // Trigger DLQ for specific productId
        List<Map<String, Object>> items = (List<Map<String, Object>>) event.getPayload().get("items");
        if (items != null) {{
            for (Map<String, Object> item : items) {{
                if ("FAIL-ME".equals(item.get("productId"))) {{
                    throw new AmqpRejectAndDontRequeueException("Simulating failure for DLQ");
                }}
            }}
        }}
        
        processedEventRepository.save(new ProcessedEvent(event.getEventId(), LocalDateTime.now().toString()));
        
        Event outEvent = new Event(
            UUID.randomUUID().toString(),
            "InventoryReserved",
            LocalDateTime.now().atOffset(ZoneOffset.UTC).toString(),
            event.getAggregateId(),
            event.getPayload()
        );
        rabbitTemplate.convertAndSend("order_exchange", "inventory.reserved", outEvent);
    }}
}}
""")


# SHIPPING SERVICE
pkg = "shippingservice"
base = f"shipping-service/src/main/java/com/example/{pkg}"
write_file(f"{base}/dto/Event.java", get_event_class(pkg))
write_file(f"{base}/domain/ProcessedEvent.java", get_processed_event_class(pkg))
write_file(f"{base}/repository/ProcessedEventRepository.java", get_processed_event_repo(pkg))

write_file(f"{base}/config/RabbitMQConfig.java", f"""
package com.example.{pkg}.config;
import org.springframework.amqp.core.*;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitMQConfig {{
    @Bean
    public TopicExchange exchange() {{ return new TopicExchange("order_exchange", true, false); }}
    @Bean
    public Queue shippingQueue() {{ return new Queue("shipping.queue", true); }}
    @Bean
    public Binding binding() {{ return BindingBuilder.bind(shippingQueue()).to(exchange()).with("inventory.reserved"); }}
    @Bean
    public MessageConverter converter() {{ return new Jackson2JsonMessageConverter(); }}
}}
""")

write_file(f"{base}/service/ShippingService.java", f"""
package com.example.{pkg}.service;
import com.example.{pkg}.dto.Event;
import com.example.{pkg}.domain.ProcessedEvent;
import com.example.{pkg}.repository.ProcessedEventRepository;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.time.LocalDateTime;
import java.time.ZoneOffset;
import java.util.UUID;

@Service
public class ShippingService {{
    @Autowired
    private ProcessedEventRepository processedEventRepository;
    @Autowired
    private RabbitTemplate rabbitTemplate;

    @Transactional
    @RabbitListener(queues = "shipping.queue")
    public void processShipping(Event event) {{
        if (processedEventRepository.existsById(event.getEventId())) {{
            System.out.println("Event already processed: " + event.getEventId());
            return;
        }}
        
        processedEventRepository.save(new ProcessedEvent(event.getEventId(), LocalDateTime.now().toString()));
        
        Event outEvent = new Event(
            UUID.randomUUID().toString(),
            "ShipmentCreated",
            LocalDateTime.now().atOffset(ZoneOffset.UTC).toString(),
            event.getAggregateId(),
            event.getPayload()
        );
        rabbitTemplate.convertAndSend("order_exchange", "shipment.created", outEvent);
    }}
}}
""")

# NOTIFICATION SERVICE
pkg = "notificationservice"
base = f"notification-service/src/main/java/com/example/{pkg}"
write_file(f"{base}/dto/Event.java", get_event_class(pkg))

write_file(f"{base}/config/RabbitMQConfig.java", f"""
package com.example.{pkg}.config;
import org.springframework.amqp.core.*;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitMQConfig {{
    @Bean
    public TopicExchange exchange() {{ return new TopicExchange("order_exchange", true, false); }}
    
    @Bean
    public Queue notificationQueue() {{ return new Queue("notification.queue", true); }}
    
    // Bind to all events
    @Bean
    public Binding bindOrder() {{ return BindingBuilder.bind(notificationQueue()).to(exchange()).with("order.created"); }}
    @Bean
    public Binding bindPayment() {{ return BindingBuilder.bind(notificationQueue()).to(exchange()).with("payment.processed"); }}
    @Bean
    public Binding bindInventory() {{ return BindingBuilder.bind(notificationQueue()).to(exchange()).with("inventory.reserved"); }}
    @Bean
    public Binding bindShipment() {{ return BindingBuilder.bind(notificationQueue()).to(exchange()).with("shipment.created"); }}
    
    @Bean
    public MessageConverter converter() {{ return new Jackson2JsonMessageConverter(); }}
}}
""")

write_file(f"{base}/service/NotificationService.java", f"""
package com.example.{pkg}.service;
import com.example.{pkg}.dto.Event;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Service;

@Service
public class NotificationService {{
    @RabbitListener(queues = "notification.queue")
    public void processNotification(Event event) {{
        System.out.println(String.format("Notification sent for event: %s, Order ID: %s", 
            event.getEventType(), event.getAggregateId()));
    }}
}}
""")

print("Logic generation complete.")
