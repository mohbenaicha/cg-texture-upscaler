generator_constructor_args = [
    {
        "num_in_ch": in_channels,
        "scale": scale,
        # the following are fixed model inputs
        "num_out_ch": 3,
        "num_feat": 64,
        "num_block": 23,
        "num_grow_ch": 32,
        
    }
    for in_channels, scale in zip(
        [3, 3, 3, 
         1,   # erroneous config
         3], 
         [1, 2, 4, 
          2, 
          6]  # erroneous config
    )
]
