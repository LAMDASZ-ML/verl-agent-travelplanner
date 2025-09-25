set -x
ENGINE=${1:-vllm}
# export VLLM_ATTENTION_BACKEND=XFORMERS
export CUDA_VISIBLE_DEVICES=0,1
# export SWANLAB_RESUME=must
# export SWANLAB_RUN_ID=kcdmk1hg8g49en2s5l5io
train_data_size=4
val_data_size=32
group_size=8

#  only use data preparation to indicate the modality and the data size.
python3 -m examples.data_preprocess.prepare \
    --mode 'text' \
    --train_data_size $train_data_size \
    --val_data_size $val_data_size

max_prompt_length=8192
max_response_length=2048
max_token_length=$((max_prompt_length + max_response_length))

python3 -m verl.trainer.main_ppo \
    algorithm.gamma=0.95 \
    algorithm.adv_estimator=gigpo \
    algorithm.gigpo.mode='mean_std_norm'\
    data.train_files=$HOME/data/verl-agent/text/train.parquet \
    data.val_files=$HOME/data/verl-agent/text/test.parquet \
    data.train_batch_size=$train_data_size \
    data.val_batch_size=$val_data_size \
    data.max_prompt_length=$max_prompt_length \
    data.max_response_length=$max_response_length \
    data.filter_overlong_prompts=True \
    data.truncation='error' \
    data.return_raw_chat=True \
    actor_rollout_ref.model.path=Qwen/Qwen2.5-1.5B-Instruct\
    actor_rollout_ref.actor.optim.lr=5e-6 \
    actor_rollout_ref.model.use_remove_padding=True \
    actor_rollout_ref.model.use_fused_kernels=True \
    actor_rollout_ref.actor.ppo_mini_batch_size=32 \
    actor_rollout_ref.actor.ppo_micro_batch_size_per_gpu=8 \
    actor_rollout_ref.actor.use_kl_loss=True \
    actor_rollout_ref.actor.kl_loss_coef=0.01 \
    actor_rollout_ref.actor.kl_loss_type=low_var_kl \
    actor_rollout_ref.model.enable_gradient_checkpointing=True \
    actor_rollout_ref.model.enable_activation_offload=True \
    actor_rollout_ref.rollout.log_prob_micro_batch_size_per_gpu=16 \
    actor_rollout_ref.rollout.tensor_model_parallel_size=1 \
    actor_rollout_ref.rollout.name=$ENGINE \
    actor_rollout_ref.rollout.gpu_memory_utilization=0.8 \
    actor_rollout_ref.rollout.max_num_batched_tokens=$max_token_length \
    actor_rollout_ref.actor.ppo_max_token_len_per_gpu=$max_token_len \
    actor_rollout_ref.ref.log_prob_max_token_len_per_gpu=$max_token_len \
    actor_rollout_ref.rollout.log_prob_max_token_len_per_gpu=$max_token_len \
    actor_rollout_ref.rollout.enable_chunked_prefill=True \
    actor_rollout_ref.rollout.enforce_eager=False \
    actor_rollout_ref.rollout.free_cache_engine=False \
    actor_rollout_ref.rollout.val_kwargs.temperature=0.7 \
    actor_rollout_ref.rollout.val_kwargs.temperature=0.7 \
    actor_rollout_ref.rollout.val_kwargs.do_sample=True \
    actor_rollout_ref.ref.log_prob_micro_batch_size_per_gpu=16 \
    actor_rollout_ref.ref.fsdp_config.param_offload=True \
    actor_rollout_ref.actor.use_invalid_action_penalty=True \
    actor_rollout_ref.actor.invalid_action_penalty_coef=0.01 \
    algorithm.use_kl_in_reward=False \
    env.env_name=MEM1Travelplanner \
    env.seed=0 \
    env.max_steps=30 \
    env.rollout.n=$group_size \
    trainer.logger=['console','swanlab'] \
    trainer.project_name='verl_agent_travelplanner' \
    trainer.experiment_name='gigpo_qwen2.5_1.5b_long_with_action_and_plan_penalty_episode_norm_plan_fulfill_rate' \
    trainer.n_gpus_per_node=2 \
    trainer.nnodes=1 \
    trainer.save_freq=5 \
    trainer.test_freq=5 \
    trainer.total_epochs=200 \
    trainer.max_actor_ckpt_to_keep=1\
    trainer.val_before_train=False \
    actor_rollout_ref.actor.fsdp_config.param_offload=True \
    actor_rollout_ref.actor.fsdp_config.optimizer_offload=True \
    +actor_rollout_ref.ref.fsdp_config.model_dtype=bf16 \
    +actor_rollout_ref.actor.fsdp_config.model_dtype=bf16 \
    +reward_model.normalize_by_length=True \