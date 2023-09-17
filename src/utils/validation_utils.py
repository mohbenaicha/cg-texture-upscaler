import os
import inspect
from typing import List, Optional, Tuple
from pydantic import BaseModel, ValidationError
from app_config.config import ExportConfig
from model.utils import write_log_to_file

log_file = write_log_to_file(None, None, None)

def validate_export_config(
    *,
    export_config: ExportConfig,
) -> Tuple[dict, Optional[dict]]:
    """Validates that export config is as expected according to a defined
    Pydantic schema."""

    errors = None
    config_obj = dict()
    for member in list(inspect.get_annotations(export_config)):
        config_obj[member] = export_config.__dict__.get(member, None)
    
    if not os.path.isdir(config_obj['single_export_location']) and not config_obj['save_in_existing_location']:
        errors = f"Invalid export path: {config_obj['single_export_location']}"
        write_log_to_file("Error", errors, log_file)
    try:
        ExportConfigSchema(**config_obj)
    except ValidationError as error:
        errors = error.json()
        write_log_to_file("Error", f"Invalid export configuration: {config_obj}", log_file)
    return config_obj, errors


def validate_variable_gen_args(generator_args: dict):
    """Validates that variable generator model consructor arguments are as
    expected according to a fixed pydantic schema"""
    errors = None
    try:
        ExportConfigSchema(**generator_args)
    except ValidationError as error:
        errors = error.json()
    
    return generator_args, errors


# for testing prediction
class ExportConfigSchema(BaseModel):
    available_devices: Optional[List[str]]
    device: Optional[str]  
    scale: Optional[str]  
    export_format: Optional[str]  
    compression: Optional[str]  
    active_compression: Optional[Tuple[str,str]]
    mipmaps: Optional[str]  
    save_prefix: Optional[str]  
    save_suffix: Optional[str]  
    save_numbering: Optional[bool]  
    save_in_existing_location: Optional[bool]  
    single_export_location: Optional[str]
    weight_file: Optional[str]
    noise_level: Optional[float]


class GeneratorArgumentSchema(BaseModel):
    scale: int
    in_channels: int
    out_channels: int


if __name__ == "__main__":
    validate_export_config(export_config=ExportConfig)
