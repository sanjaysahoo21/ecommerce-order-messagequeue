package com.example.orderservice.config;
import org.springframework.amqp.core.*;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitMQConfig {
    public static final String EXCHANGE = "order_exchange";
    public static final String QUEUE_ORDER_CREATED = "order.created.queue";
    
    @Bean
    public TopicExchange exchange() { return new TopicExchange(EXCHANGE, true, false); }
    
    @Bean
    public Queue orderCreatedQueue() { return new Queue(QUEUE_ORDER_CREATED, true); }
    
    @Bean
    public Binding bindingOrderCreated() { return BindingBuilder.bind(orderCreatedQueue()).to(exchange()).with("order.created"); }
    
    // Queues to listen for status updates
    @Bean
    public Queue paymentProcessedStatusQueue() { return new Queue("order.status.payment.queue", true); }
    @Bean
    public Binding bindingPaymentStatus() { return BindingBuilder.bind(paymentProcessedStatusQueue()).to(exchange()).with("payment.processed"); }
    
    @Bean
    public Queue inventoryReservedStatusQueue() { return new Queue("order.status.inventory.queue", true); }
    @Bean
    public Binding bindingInventoryStatus() { return BindingBuilder.bind(inventoryReservedStatusQueue()).to(exchange()).with("inventory.reserved"); }
    
    @Bean
    public Queue shipmentCreatedStatusQueue() { return new Queue("order.status.shipment.queue", true); }
    @Bean
    public Binding bindingShipmentStatus() { return BindingBuilder.bind(shipmentCreatedStatusQueue()).to(exchange()).with("shipment.created"); }
    
    @Bean
    public MessageConverter converter() { return new Jackson2JsonMessageConverter(); }
}