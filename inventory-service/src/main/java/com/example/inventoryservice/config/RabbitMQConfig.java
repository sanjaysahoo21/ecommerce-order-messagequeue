package com.example.inventoryservice.config;
import org.springframework.amqp.core.*;
import org.springframework.amqp.support.converter.Jackson2JsonMessageConverter;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RabbitMQConfig {
    @Bean
    public TopicExchange exchange() { return new TopicExchange("order_exchange", true, false); }
    
    @Bean
    public TopicExchange dlx() { return new TopicExchange("dlx_exchange", true, false); }
    
    @Bean
    public Queue dlq() { return new Queue("inventory.dlq", true); }
    
    @Bean
    public Binding dlqBinding() { return BindingBuilder.bind(dlq()).to(dlx()).with("inventory.dlq.key"); }
    
    @Bean
    public Queue inventoryQueue() { 
        return QueueBuilder.durable("inventory.queue")
                           .withArgument("x-dead-letter-exchange", "dlx_exchange")
                           .withArgument("x-dead-letter-routing-key", "inventory.dlq.key")
                           .build(); 
    }
    
    @Bean
    public Binding binding() { return BindingBuilder.bind(inventoryQueue()).to(exchange()).with("payment.processed"); }
    @Bean
    public MessageConverter converter() { return new Jackson2JsonMessageConverter(); }
}