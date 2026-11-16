import { Menu } from "@base-ui/react/menu"

import { cn } from "@/lib/utils"

// The shadcn dropdown menu, Base UI variant (ui.shadcn.com/docs/components/base/dropdown-menu), themed with the console
// tokens: a 12px popover on the e3 shadow, 8px items, a destructive item in the risk colour, 44px rows on touch.
function DropdownMenu(props: Menu.Root.Props) {
  return <Menu.Root data-slot="dropdown-menu" {...props} />
}

function DropdownMenuTrigger(props: Menu.Trigger.Props) {
  return <Menu.Trigger data-slot="dropdown-menu-trigger" {...props} />
}

function DropdownMenuContent({
  align = "end",
  alignOffset = 0,
  side = "bottom",
  sideOffset = 6,
  className,
  ...props
}: Menu.Popup.Props & Pick<Menu.Positioner.Props, "align" | "alignOffset" | "side" | "sideOffset">) {
  return (
    <Menu.Portal>
      <Menu.Positioner align={align} alignOffset={alignOffset} side={side} sideOffset={sideOffset} className="z-60 outline-none">
        <Menu.Popup
          data-slot="dropdown-menu-content"
          className={cn(
            "min-w-60 max-w-[22rem] origin-(--transform-origin) rounded-card border border-border bg-popover p-1.5 text-popover-foreground shadow-e3 outline-none",
            "transition-[opacity,transform] duration-100 data-[starting-style]:scale-95 data-[starting-style]:opacity-0 data-[ending-style]:scale-95 data-[ending-style]:opacity-0",
            className,
          )}
          {...props}
        />
      </Menu.Positioner>
    </Menu.Portal>
  )
}

function DropdownMenuGroup(props: Menu.Group.Props) {
  return <Menu.Group data-slot="dropdown-menu-group" {...props} />
}

function DropdownMenuLabel({ className, ...props }: Menu.GroupLabel.Props) {
  return <Menu.GroupLabel data-slot="dropdown-menu-label" className={cn("t-overline px-2.5 pb-1 pt-2", className)} {...props} />
}

function DropdownMenuItem({ className, variant = "default", ...props }: Menu.Item.Props & { variant?: "default" | "destructive" }) {
  return (
    <Menu.Item
      data-slot="dropdown-menu-item"
      data-variant={variant}
      className={cn(
        "flex min-h-10 cursor-default select-none items-center gap-2.5 rounded-control px-2.5 py-1.5 text-[13px] outline-none",
        "data-[highlighted]:bg-hover data-[disabled]:pointer-events-none data-[disabled]:opacity-50",
        "[&_svg]:size-4 [&_svg]:shrink-0 [&_svg]:text-muted-foreground",
        variant === "destructive" && "text-risk-text data-[highlighted]:bg-risk-bg [&_svg]:text-risk",
        className,
      )}
      {...props}
    />
  )
}

function DropdownMenuSeparator({ className, ...props }: Menu.Separator.Props) {
  return <Menu.Separator data-slot="dropdown-menu-separator" className={cn("-mx-1.5 my-1.5 h-px bg-divider", className)} {...props} />
}

export { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuGroup, DropdownMenuLabel, DropdownMenuItem, DropdownMenuSeparator }
