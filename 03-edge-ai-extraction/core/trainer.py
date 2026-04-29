"""
LoRA fine-tuning logic for receipt field extraction.

Uses HuggingFace PEFT to add LoRA adapters to a base model.
"""

import os


def get_training_config() -> dict:
    """
    Return the LoRA + training configuration.

    These defaults are tuned for:
    - Phi-3-mini base model
    - 4-bit quantization (fits on 16GB VRAM)
    - ~626 training samples (SROIE dataset)
    """
    return {
        # LoRA config
        "lora_r": 16,
        "lora_alpha": 32,
        "lora_dropout": 0.05,
        "target_modules": ["q_proj", "v_proj", "k_proj", "o_proj"],
        # Training config
        "base_model": "microsoft/Phi-3-mini-4k-instruct",
        "num_epochs": 3,
        "batch_size": 4,
        "learning_rate": 2e-4,
        "max_seq_length": 512,
        "gradient_accumulation_steps": 4,
        # Quantization
        "load_in_4bit": True,
        "bnb_4bit_compute_dtype": "float16",
        # Output
        "output_dir": "models/receipt-lora-adapter",
    }


def train(train_path: str, val_path: str):
    """
    Run LoRA fine-tuning on the receipt extraction task.

    Args:
        train_path: Path to training JSONL file.
        val_path: Path to validation JSONL file.
    """
    try:
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            TrainingArguments,
            Trainer,
        )
        from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
        from datasets import load_dataset
        import torch
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Install: pip install transformers peft datasets torch bitsandbytes")
        return

    config = get_training_config()

    print(f"📦 Loading base model: {config['base_model']}")
    tokenizer = AutoTokenizer.from_pretrained(config["base_model"])
    tokenizer.pad_token = tokenizer.eos_token

    # Load model with quantization
    model = AutoModelForCausalLM.from_pretrained(
        config["base_model"],
        load_in_4bit=config["load_in_4bit"],
        device_map="auto",
        torch_dtype=torch.float16,
    )

    model = prepare_model_for_kbit_training(model)

    # Apply LoRA
    lora_config = LoraConfig(
        r=config["lora_r"],
        lora_alpha=config["lora_alpha"],
        lora_dropout=config["lora_dropout"],
        target_modules=config["target_modules"],
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # Load dataset
    dataset = load_dataset("json", data_files={"train": train_path, "val": val_path})

    def tokenize(example):
        text = f"### Receipt:\n{example['input']}\n\n### Extracted Fields:\n{example['output']}"
        return tokenizer(text, truncation=True, max_length=config["max_seq_length"])

    tokenized = dataset.map(tokenize, remove_columns=dataset["train"].column_names)

    # Training
    training_args = TrainingArguments(
        output_dir=config["output_dir"],
        num_train_epochs=config["num_epochs"],
        per_device_train_batch_size=config["batch_size"],
        gradient_accumulation_steps=config["gradient_accumulation_steps"],
        learning_rate=config["learning_rate"],
        fp16=True,
        logging_steps=10,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["val"],
    )

    print("🚀 Starting LoRA fine-tuning...")
    trainer.train()

    # Save adapter
    model.save_pretrained(config["output_dir"])
    tokenizer.save_pretrained(config["output_dir"])
    print(f"✅ Adapter saved to {config['output_dir']}")
