package com.example.orderservice.controller;
import com.example.orderservice.domain.Order;
import com.example.orderservice.repository.OrderRepository;
import com.example.orderservice.dto.Event;
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
public class OrderController {
    @Autowired
    private OrderRepository orderRepository;
    @Autowired
    private RabbitTemplate rabbitTemplate;
    @Autowired
    private ObjectMapper objectMapper;

    @PostMapping
    public ResponseEntity<Map<String, String>> createOrder(@RequestBody Map<String, Object> request) throws Exception {
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
    }

    @GetMapping("/{id}")
    public ResponseEntity<?> getOrder(@PathVariable String id) {
        return orderRepository.findById(id)
                .map(order -> ResponseEntity.ok(order))
                .orElse(ResponseEntity.notFound().build());
    }
}