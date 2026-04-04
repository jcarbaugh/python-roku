import asyncio

import click


@click.group()
@click.option("--async", "use_async", is_flag=True, default=False, help="Use async client")
@click.pass_context
def cli(ctx, use_async):
    ctx.ensure_object(dict)
    ctx.obj["use_async"] = use_async


@cli.command()
@click.option("--timeout", type=int, default=2, help="Discovery timeout in seconds")
@click.option("--retries", type=int, default=1, help="Number of retries")
@click.option("-i", "--inspect", is_flag=True, default=False, help="Fetch and display device details")
@click.pass_context
def discover(ctx, timeout, retries, inspect):
    """Discover Roku devices on the network."""
    if ctx.obj["use_async"]:
        from roku._async.core import AsyncRoku

        rokus = asyncio.run(AsyncRoku.discover(timeout=timeout, retries=retries))
    else:
        from roku.core import Roku

        rokus = Roku.discover(timeout=timeout, retries=retries)

    if not rokus:
        click.echo("No Roku devices found.")
        return

    for roku in rokus:
        click.echo(f"{roku.host}:{roku.port}")
        if inspect:
            if ctx.obj["use_async"]:

                async def _get_info(r):
                    async with r:
                        return await r.get_device_info()

                info = asyncio.run(_get_info(roku))
            else:
                info = roku.device_info
            click.echo(f"  Name:     {info.user_device_name}")
            click.echo(f"  Model:    {info.model_name} ({info.model_num})")
            click.echo(f"  Type:     {info.roku_type}")
            click.echo(f"  Software: {info.software_version}")
            click.echo(f"  Serial:   {info.serial_num}")
