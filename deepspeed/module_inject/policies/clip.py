import torch
from torch.nn.parameter import Parameter
from ..policy import TransformerPolicy


class HFCLIPLayerPolicy(TransformerPolicy):
    def __init__(self, client_module, inference=False):
        super().__init__(inference, pre_attn_norm=True, scale_attention=True)
        self.client_module = client_module
        self.cuda_graph_supported = True

        if HFCLIPLayerPolicy._orig_layer_class is None:
            try:
                import transformers
                HFCLIPLayerPolicy._orig_layer_class = transformers.models.clip.modeling_clip.CLIPEncoderLayer
            except:
                HFCLIPLayerPolicy._orig_layer_class = None

    def get_hidden_heads(self):
        return self.client_module.self_attn.q_proj.weight.shape[1], \
                self.client_module.self_attn.num_heads

    def attention(self):
        qw = self.client_module.self_attn.q_proj.weight
        qb = self.client_module.self_attn.q_proj.bias
        kw = self.client_module.self_attn.k_proj.weight
        kb = self.client_module.self_attn.k_proj.bias
        vw = self.client_module.self_attn.v_proj.weight
        vb = self.client_module.self_attn.v_proj.bias

        qkvw = Parameter(torch.cat((qw, kw, vw), dim=0), requires_grad=False)
        qkvb = Parameter(torch.cat((qb, kb, vb), dim=0), requires_grad=False)

        return self.linear_layer, \
               qkvw, \
               qkvb, \
               self.client_module.self_attn.out_proj.weight, \
               self.client_module.self_attn.out_proj.bias, \
               self.scale_attention, \
               self.is_megatron_v2

    def mlp(self):
        return self.linear_layer, \
            self.client_module.mlp.fc1.weight, \
            self.client_module.mlp.fc1.bias, \
            self.client_module.mlp.fc2.weight, \
            self.client_module.mlp.fc2.bias

    def layerNorm(self):
        return self.client_module.layer_norm2.weight, \
               self.client_module.layer_norm2.bias, \
               self.client_module.layer_norm1.weight, \
               self.client_module.layer_norm1.bias
