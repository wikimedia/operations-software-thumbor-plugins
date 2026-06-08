import ecs_logging


class ThumborFormatter(ecs_logging.StdlibFormatter):
    """Formats log records as ECS-compliant JSON.

    Remap a few of the things we add in `extras` to be a bit more
    ECS-friendly. In the long run those should be cleaned up more
    generally.
    """

    # Custom record attribute -> ECS field name.
    ECS_FIELD_MAP = {
        "url": "url.original",
        "thumbor-request-id": "http.request.id",
        "port": "service.node.name",
        "thumbor-version": "labels.thumbor_version",
        "wikimedia-thumbor-version": "service.version",
        "traceback": "error.stack_trace",
    }

    def format_to_ecs(self, record):
        for src, dst in self.ECS_FIELD_MAP.items():
            if src in record.__dict__ and record.__dict__[src]:
                record.__dict__[dst] = record.__dict__.pop(src)

        return super(ThumborFormatter, self).format_to_ecs(record)
