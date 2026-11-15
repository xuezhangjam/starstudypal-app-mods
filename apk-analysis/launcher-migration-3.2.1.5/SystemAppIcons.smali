.class public final Lcom/hljzjx/md3/SystemAppIcons;
.super Ljava/lang/Object;

.method public static bindModel(Landroid/content/Context;Lcom/hailiang/launcher/data/bean/response/AppHtmlListBean;Landroid/widget/ImageView;)Z
    .locals 2
    if-eqz p1, :skip
    invoke-virtual {p1}, Lcom/hailiang/launcher/data/bean/response/AppHtmlListBean;->isWeb()Z
    move-result v0
    if-nez v0, :skip
    invoke-virtual {p1}, Lcom/hailiang/launcher/data/bean/response/AppHtmlListBean;->getPackageName()Ljava/lang/String;
    move-result-object p1
    const/4 v0, 0x1
    invoke-static {p0, p1, p2, v0}, Lcom/hljzjx/md3/SystemAppIcons;->bind(Landroid/content/Context;Ljava/lang/String;Landroid/widget/ImageView;Z)Z
    move-result v0
    return v0
    :skip
    const/4 v0, 0x0
    return v0
.end method

.method public static bindInstalled(Landroid/content/Context;Ljava/lang/String;Landroid/widget/ImageView;)Z
    .locals 1
    const/4 v0, 0x0
    invoke-static {p0, p1, p2, v0}, Lcom/hljzjx/md3/SystemAppIcons;->bind(Landroid/content/Context;Ljava/lang/String;Landroid/widget/ImageView;Z)Z
    move-result v0
    return v0
.end method

.method private static bind(Landroid/content/Context;Ljava/lang/String;Landroid/widget/ImageView;Z)Z
    .locals 2
    if-eqz p0, :skip
    if-eqz p2, :skip
    invoke-virtual {p0}, Landroid/content/Context;->getPackageManager()Landroid/content/pm/PackageManager;
    move-result-object v0
    :read_start
    invoke-virtual {v0, p1}, Landroid/content/pm/PackageManager;->getApplicationIcon(Ljava/lang/String;)Landroid/graphics/drawable/Drawable;
    move-result-object v1
    :read_end
    .catch Ljava/lang/Exception; {:read_start .. :read_end} :missing
    if-nez v1, :bind
    goto :fallback
    :missing
    move-exception v1
    :fallback
    if-eqz p3, :skip
    invoke-virtual {v0}, Landroid/content/pm/PackageManager;->getDefaultActivityIcon()Landroid/graphics/drawable/Drawable;
    move-result-object v1
    :bind
    invoke-static {p0}, Lcom/bumptech/glide/Glide;->with(Landroid/content/Context;)Lcom/bumptech/glide/RequestManager;
    move-result-object v0
    invoke-virtual {v0, p2}, Lcom/bumptech/glide/RequestManager;->clear(Landroid/view/View;)V
    invoke-virtual {p2, v1}, Landroid/widget/ImageView;->setImageDrawable(Landroid/graphics/drawable/Drawable;)V
    const/4 v0, 0x1
    return v0
    :skip
    const/4 v0, 0x0
    return v0
.end method
